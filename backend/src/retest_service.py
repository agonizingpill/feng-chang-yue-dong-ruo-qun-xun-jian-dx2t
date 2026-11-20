from datetime import datetime
import uuid
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from .models import Visit,RetestOrder,Retest,Audit,Reading,Hive,CareAction
from .yard_service import require
from .screen_model import assess_reading

def open_order(db,visit,reading,actor):
    """筛查后为跨异常线的巡检建立待复测单；同箱已有待复测单则沿用原依据。"""
    breakdown=reading.breakdown or {}
    if not breakdown.get('crosses'):return None
    existing=db.scalar(select(RetestOrder).where(RetestOrder.hive_id==visit.hive_id,RetestOrder.state=='pending'))
    if existing:return existing
    order=RetestOrder(code='RT-tmp-'+uuid.uuid4().hex[:12],hive_id=visit.hive_id,initial_visit_id=visit.id,initial_weight_kg=visit.weight_kg,
        initial_temperature=visit.temperature,initial_weight_error_kg=reading.weight_error_kg,
        initial_temperature_error_c=reading.temperature_error_c,initial_activity=visit.activity,
        initial_feed_left=visit.feed_left,initial_breakdown=breakdown,created_by=actor,version=0)
    db.add(order);db.flush();order.code=f'RT-{order.id:04}'
    hive=db.get(Hive,visit.hive_id)
    if hive:hive.care_state='retest_pending'
    db.add(Audit(actor=actor,action=f'巡检 {visit.code} 跨异常线，转待复测 {order.code}'))
    return order

def resolve(db,order,user):
    """复测未跨线后结束待复测，巡检保留原依据；无进行中处置才更新箱况。"""
    order.state='resolved';order.closed_at=datetime.utcnow()
    visit=require(db,Visit,order.initial_visit_id)
    hive=db.get(Hive,visit.hive_id)
    active=db.scalar(select(CareAction.id).where(CareAction.visit_id==visit.id,
        CareAction.status.in_(['planned','executed','rechecked','needs_requeen'])))
    if hive and visit.status=='screened' and not active:
        hive.care_state='needs_care' if visit.anomaly_flag or not visit.queen_seen else 'observe'
    db.add(Audit(actor=user.email,action=f'待复测单 {order.code} 未跨异常线，结束待复测，初测依据保留'))

def pending_for_hive(db,hive_id):
    return db.scalar(select(RetestOrder).where(RetestOrder.hive_id==hive_id,RetestOrder.state=='pending'))

def record(db,key,body,user):
    order=require(db,RetestOrder,key,True)
    replay=db.scalar(select(Retest).where(Retest.request_id==body.request_id))
    if replay:
        if replay.order_id!=key:raise HTTPException(409,'请求编号已用于其他待复测单')
        return replay
    if order.state!='pending':raise HTTPException(409,'该待复测单已完成，不再接收补测')
    if body.expected_version!=order.version:
        raise HTTPException(409,'待复测单已收到另一份补测，请刷新后再登记')
    visit=require(db,Visit,order.initial_visit_id)
    breakdown=assess_reading(weight_kg=body.weight_kg,temperature=body.temperature,
        weight_error_kg=body.weight_error_kg,temperature_error_c=body.temperature_error_c,
        activity=visit.activity,feed_left=visit.feed_left)
    breakdown.pop('evidence',None)
    attempt=(db.scalar(select(Retest.attempt).where(Retest.order_id==order.id).order_by(Retest.attempt.desc())) or 0)+1
    retest=Retest(order_id=order.id,attempt=attempt,request_id=body.request_id,weight_kg=body.weight_kg,
        temperature=body.temperature,weight_error_kg=body.weight_error_kg,
        temperature_error_c=body.temperature_error_c,breakdown=breakdown,
        crosses_threshold=breakdown['crosses'],recorded_by=user.email)
    order.version=order.version+1
    if breakdown['crosses']:
        order.state='pending'
    else:
        resolve(db,order,user)
    db.add(retest)
    db.add(Audit(actor=user.email,action=f'待复测单 {order.code} 第{attempt}次补测 {body.weight_kg}kg/{body.temperature}°C，'
        +('仍跨线，继续待复测' if breakdown['crosses'] else '未跨线，待复测结束')))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        replay=db.scalar(select(Retest).where(Retest.request_id==body.request_id))
        if replay and replay.order_id==key:return replay
        raise HTTPException(409,'待复测单已被另一份补测占用，请刷新后重试')
    return retest
