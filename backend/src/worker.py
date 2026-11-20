import os,json,traceback
from pathlib import Path
import redis
from sqlalchemy import select
from .database import Session
from .models import Visit,Hive,Reading
from .screen_model import screen,reference_model
from .retest_service import open_order
from .yard_service import latest
queue=redis.Redis.from_url(os.getenv('REDIS_URL','redis://redis:6379/0'),decode_responses=True)
while True:
    Path('/tmp/apiary-heartbeat').touch();job=queue.blpop('apiary:screening',timeout=3)
    if not job:continue
    task=json.loads(job[1]);points=[];evidence=reference_model()[1]
    try:
        for key in task['visit_ids']:
            Path('/tmp/apiary-heartbeat').touch()
            with Session() as db:
                visit=db.scalar(select(Visit).where(Visit.id==key).with_for_update())
                if not visit or visit.status!='screening':continue
                reading=db.scalar(select(Reading).where(Reading.visit_id==visit.id).with_for_update())
                if not reading:
                    visit.status='blocked';db.commit();continue
                score,flag,margin,evidence,breakdown=screen(reading,visit)
                reading.breakdown=breakdown;reading.crosses_threshold=flag
                visit.anomaly_score=score;visit.anomaly_flag=flag;visit.decision_margin=margin;visit.model_evidence=evidence;visit.status='screened'
                hive=db.get(Hive,visit.hive_id)
                if latest(db,hive.id)==visit.id:hive.care_state='needs_care' if flag or not visit.queen_seen else 'observe'
                order=open_order(db,visit,reading,reading.created_by)
                db.commit()
                points.append({'visit_id':visit.id,'hive_id':hive.id,'score':score,'flag':flag,
                    'crosses':flag,'original':breakdown['original'],'variants':breakdown['variants'],
                    'worst_score':breakdown['worst_score'],'retest_order_id':order.id if order else None})
        result={'status':'done','count':len(points),'points':points,'evidence':evidence}
        Path('/artifacts').mkdir(exist_ok=True);Path(f"/artifacts/screen-{task['job_id']}.json").write_text(json.dumps(result))
        queue.set('apiary:screen:'+task['job_id'],json.dumps(result),ex=86400)
    except Exception as error:
        traceback.print_exc();queue.set('apiary:screen:'+task['job_id'],json.dumps({'status':'failed','error':str(error)}),ex=86400)
        with Session() as db:
            for v in db.scalars(select(Visit).where(Visit.id.in_(task['visit_ids']),Visit.status=='screening')).all():v.status='blocked'
            db.commit()
