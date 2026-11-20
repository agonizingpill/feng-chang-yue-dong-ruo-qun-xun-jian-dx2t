import json,hashlib
from pathlib import Path
from functools import lru_cache
import numpy as np
from sklearn.ensemble import IsolationForest
from .measurement import assess
FEATURES=['weight_kg','temperature','activity','feed_left']
@lru_cache(maxsize=1)
def reference_model():
    raw=(Path(__file__).resolve().parents[1]/'fixtures/winter_reference.json').read_bytes();rows=json.loads(raw)
    x=np.array([[r[k] for k in FEATURES] for r in rows])
    model=IsolationForest(n_estimators=150,contamination=.15,random_state=42,n_jobs=1)
    model.fit(x);scores=model.score_samples(x)
    evidence={'reference_rows':len(rows),'contamination':.15,'threshold':float(model.offset_),'reference_min':float(scores.min()),'reference_max':float(scores.max()),'reference_flagged':int((scores<model.offset_).sum()),'sha256':hashlib.sha256(raw).hexdigest(),'random_state':42,'method':'IsolationForest / 150 trees / score_samples'}
    return model,evidence

def assess_reading(*,weight_kg,temperature,weight_error_kg,temperature_error_c,activity,feed_left):
    model,evidence=reference_model()
    score_fn=lambda w,t,a,f:float(model.score_samples([[w,t,a,f]])[0])
    breakdown=assess(score_fn,weight_kg=weight_kg,temperature=temperature,
        weight_error_kg=weight_error_kg,temperature_error_c=temperature_error_c,
        activity=activity,feed_left=feed_left,threshold=evidence['threshold'])
    breakdown['evidence']={k:evidence[k] for k in ('reference_rows','contamination','threshold','reference_min','reference_max','reference_flagged','sha256','random_state','method')}
    return breakdown

def screen(reading,visit):
    """reading 提供两项误差，visit 提供原始读数。"""
    breakdown=assess_reading(weight_kg=visit.weight_kg,temperature=visit.temperature,
        weight_error_kg=reading.weight_error_kg,temperature_error_c=reading.temperature_error_c,
        activity=visit.activity,feed_left=visit.feed_left)
    evidence=breakdown.pop('evidence')
    original=breakdown['original']
    return original['score'],breakdown['crosses'],original['score']-evidence['threshold'],evidence,breakdown

