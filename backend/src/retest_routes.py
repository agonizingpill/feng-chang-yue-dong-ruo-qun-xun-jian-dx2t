from fastapi import APIRouter,Depends
from sqlalchemy import select
from .database import session
from .auth import current,editor
from .models import RetestOrder,Retest,Reading
from .yard_service import require
from .retest_schemas import RetestInput
from . import retest_service
router=APIRouter()

@router.get('/retest-orders')
def orders(user=Depends(current),db=Depends(session)):return db.scalars(select(RetestOrder).order_by(RetestOrder.id.desc())).all()
@router.get('/retest-orders/{key}')
def order(key:int,user=Depends(current),db=Depends(session)):
    row=require(db,RetestOrder,key)
    retests=db.scalars(select(Retest).where(Retest.order_id==key).order_by(Retest.attempt)).all()
    return {'order':row,'retests':retests}
@router.get('/retests')
def retests(user=Depends(current),db=Depends(session)):return db.scalars(select(Retest).order_by(Retest.id.desc())).all()
@router.post('/retest-orders/{key}/retests')
def record(key:int,body:RetestInput,user=Depends(editor),db=Depends(session)):return retest_service.record(db,key,body,user)
@router.get('/readings')
def readings(user=Depends(current),db=Depends(session)):return db.scalars(select(Reading).order_by(Reading.id.desc())).all()
