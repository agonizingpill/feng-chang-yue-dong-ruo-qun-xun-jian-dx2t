import {api} from './api.js';
export const book={hives:[],visits:[],care:[],lots:[],issues:[],queens:[],moves:[],insulationLots:[],installs:[],spring:[],readings:[],retestOrders:[],retests:[],selectedHive:31,selectedVisit:null,selectedCare:null,selectedRetest:null,planning:false,showAll:false,showRetestAll:false};
export async function openNotebook(){[book.hives,book.visits,book.care,book.lots,book.issues,book.queens,book.moves,book.insulationLots,book.installs,book.spring,book.readings,book.retestOrders,book.retests]=await Promise.all([api('/hives'),api('/visits'),api('/care'),api('/feed-lots'),api('/feed-issues'),api('/queen-observations'),api('/moves'),api('/insulation-lots'),api('/insulation-installs'),api('/spring-reviews'),api('/readings'),api('/retest-orders'),api('/retests')]);}
export function latestVisits(){const found=new Map();for(const visit of book.visits)if(!found.has(visit.hive_id))found.set(visit.hive_id,visit);return [...found.values()];}
export const readingFor=visitId=>book.readings.find(r=>r.visit_id===visitId);
export const pendingRetest=hiveId=>book.retestOrders.find(o=>o.hive_id===hiveId&&o.state==='pending');
export const retestsFor=orderId=>book.retests.filter(r=>r.order_id===orderId).sort((a,b)=>a.attempt-b.attempt);
export const breakdownOf=r=>r?.breakdown||null;
