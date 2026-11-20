"""低温称重与测温的误差区间评估。

冷天抬箱称重和箱温读数容易偏差，因此巡检时要同时登记两项误差。
筛查先按原始读数打分，再把体重、箱温各自展开成上下限，得到四组
组合读数与四个组合分值。原始分值或任一组组合分值低于异常阈值，
就视为“跨异常线”，蜂箱转入待复测；复测用同样口径重算。

本模块不依赖 numpy/sklearn，便于单独验证组合与跨线判断。
"""

COMBINATIONS=(
    ('weight_low_temperature_low','体重下限 / 温度下限',-1,-1),
    ('weight_low_temperature_high','体重下限 / 温度上限',-1,1),
    ('weight_high_temperature_low','体重上限 / 温度下限',1,-1),
    ('weight_high_temperature_high','体重上限 / 温度上限',1,1),
)
MIN_WEIGHT=0.01


def measurement_bounds(weight_kg,temperature,weight_error_kg,temperature_error_c):
    """返回四组体重/箱温上下限组合，体重不会低于 MIN_WEIGHT。"""
    weight=float(weight_kg);temp=float(temperature)
    weight_error=abs(float(weight_error_kg or 0));temperature_error=abs(float(temperature_error_c or 0))
    lower=max(weight-weight_error,MIN_WEIGHT);upper=weight+weight_error
    rows=[]
    for key,label,weight_sign,temperature_sign in COMBINATIONS:
        rows.append({
            'key':key,
            'label':label,
            'weight_kg':round(lower if weight_sign<0 else upper,4),
            'temperature':round(temp+temperature_sign*temperature_error,4),
        })
    return rows


def assess(score_fn,*,weight_kg,temperature,weight_error_kg,temperature_error_c,activity,feed_left,threshold):
    """计算原始分值及四种误差上下限组合分值。

    score_fn(weight, temperature, activity, feed_left) 返回模型分值。
    crosses 为 True 表示原始或任一组组合分值低于阈值，需要复测。
    """
    threshold=float(threshold)
    weight=float(weight_kg);temp=float(temperature)
    original_score=float(score_fn(weight,temp,activity,feed_left))
    variants=[]
    for row in measurement_bounds(weight,temp,weight_error_kg,temperature_error_c):
        score=float(score_fn(row['weight_kg'],row['temperature'],activity,feed_left))
        variants.append({**row,'score':score,'flag':score<threshold})
    scores=[original_score]+[row['score'] for row in variants]
    return {
        'threshold':threshold,
        'original':{
            'weight_kg':round(weight,4),'temperature':round(temp,4),
            'score':original_score,'flag':original_score<threshold,
        },
        'variants':variants,
        'worst_score':min(scores),
        'crosses':min(scores)<threshold,
        'errors':{
            'weight_kg':abs(float(weight_error_kg or 0)),
            'temperature_c':abs(float(temperature_error_c or 0)),
        },
        'method':'原始读数 + 体重/箱温误差的四种上下限组合；任一分值低于阈值即跨异常线',
    }

