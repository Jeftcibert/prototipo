const fs=require('fs'),vm=require('vm'),path=require('path');
const html=fs.readFileSync(path.join(__dirname,'..','index.html'),'utf8');
const src=html.match(/<script id="logica">([\s\S]*?)<\/script>/)[1];
const ctx={};vm.createContext(ctx);vm.runInContext(src+';this.api={evaluar,recomendar,tablaMejoras,generarReporte,validarPorcentaje,validarMinutos};',ctx);
const A=ctx.api;const py=JSON.parse(fs.readFileSync(path.join(__dirname,'py.json'),'utf8'));
let mal=0;const eq=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
for(const c of py.casos){const f=py.fichas[c.f],e=c.e;
 const ev=A.evaluar(e.cpu,e.minutos,e.ram,e.disco,e.libre);const recs=A.recomendar(e.cpu,e.minutos,e.ram,e.disco,e.libre,f);
 const tab=A.tablaMejoras(e.ram,e.disco,e.libre,f);const rep=A.generarReporte("EQ",e,ev.estado,ev.hallazgos,ev.oportunidades,recs,f,"X");
 if(ev.estado!==c.estado||!eq(ev.hallazgos,c.h)||!eq(ev.oportunidades,c.o)||!eq(recs,c.recs)||!eq(tab,c.tabla)||rep!==c.rep){mal++;if(mal<4)console.log('DIF',c.f,JSON.stringify(e),ev.estado,c.estado);}}
console.log('casos comparados:',py.casos.length,'diferencias:',mal);
let malv=0;for(const v of py.vals){let r;try{r=['ok',(v.n==='CPU'?A.validarPorcentaje(v.t,'CPU'):A.validarMinutos(v.t))]}catch(x){r=['err',x.message]}
 const pyr=v.r; const okmatch = r[0]===pyr[0] && (r[0]==='err'? r[1]===pyr[1] : Object.is(r[1],pyr[1])||r[1]===pyr[1]);
 if(!okmatch){malv++;console.log('VAL DIF',JSON.stringify(v.t),v.n,r,pyr);}}
console.log('validaciones comparadas:',py.vals.length,'diferencias:',malv);
