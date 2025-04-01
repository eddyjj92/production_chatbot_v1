import{k as O,w as T,g as P,o as v,Q as w,E as L,a3 as g,r as Q,q as k,V as x,h as R}from"./index-D-W__4lR.js";import{c as S,g as W}from"./dom-CYAEkvpQ.js";const _=[Element,String],A=[null,document,document.body,document.scrollingElement,document.documentElement];function D(e,o){let t=W(o);if(t===void 0){if(e==null)return window;t=e.closest(".scroll,.scroll-y,.overflow-auto")}return A.includes(t)?window:t}function H(e){return e===window?window.pageYOffset||window.scrollY||document.body.scrollTop||0:e.scrollTop}function C(e){return e===window?window.pageXOffset||window.scrollX||document.body.scrollLeft||0:e.scrollLeft}function V(e,o,t=0){const n=arguments[3]===void 0?performance.now():arguments[3],i=H(e);if(t<=0){i!==o&&h(e,o);return}requestAnimationFrame(s=>{const r=s-n,a=i+(o-i)/Math.max(r,t)*r;h(e,a),a!==o&&V(e,o,t-r,s)})}function q(e,o,t=0){const n=arguments[3]===void 0?performance.now():arguments[3],i=C(e);if(t<=0){i!==o&&b(e,o);return}requestAnimationFrame(s=>{const r=s-n,a=i+(o-i)/Math.max(r,t)*r;b(e,a),a!==o&&q(e,o,t-r,s)})}function h(e,o){if(e===window){window.scrollTo(window.pageXOffset||window.scrollX||document.body.scrollLeft||0,o);return}e.scrollTop=o}function b(e,o){if(e===window){window.scrollTo(o,window.pageYOffset||window.scrollY||document.body.scrollTop||0);return}e.scrollLeft=o}function $(e,o,t){if(t){V(e,o,t);return}h(e,o)}function j(e,o,t){if(t){q(e,o,t);return}b(e,o)}let p;function B(){if(p!==void 0)return p;const e=document.createElement("p"),o=document.createElement("div");S(e,{width:"100%",height:"200px"}),S(o,{position:"absolute",top:"0px",left:"0px",visibility:"hidden",width:"200px",height:"150px",overflow:"hidden"}),o.appendChild(e),document.body.appendChild(o);const t=e.offsetWidth;o.style.overflow="scroll";let n=e.offsetWidth;return t===n&&(n=o.clientWidth),o.remove(),p=t-n,p}const{passive:z}=g,F=["both","horizontal","vertical"],I=O({name:"QScrollObserver",props:{axis:{type:String,validator:e=>F.includes(e),default:"vertical"},debounce:[String,Number],scrollTarget:_},emits:["scroll"],setup(e,{emit:o}){const t={position:{top:0,left:0},direction:"down",directionChanged:!1,delta:{top:0,left:0},inflectionPoint:{top:0,left:0}};let n=null,i,s;T(()=>e.scrollTarget,()=>{l(),a()});function r(){n?.();const u=Math.max(0,H(i)),m=C(i),d={top:u-t.position.top,left:m-t.position.left};if(e.axis==="vertical"&&d.top===0||e.axis==="horizontal"&&d.left===0)return;const y=Math.abs(d.top)>=Math.abs(d.left)?d.top<0?"up":"down":d.left<0?"left":"right";t.position={top:u,left:m},t.directionChanged=t.direction!==y,t.delta=d,t.directionChanged===!0&&(t.direction=y,t.inflectionPoint=t.position),o("scroll",{...t})}function a(){i=D(s,e.scrollTarget),i.addEventListener("scroll",c,z),c(!0)}function l(){i!==void 0&&(i.removeEventListener("scroll",c,z),i=void 0)}function c(u){if(u===!0||e.debounce===0||e.debounce==="0")r();else if(n===null){const[m,d]=e.debounce?[setTimeout(r,e.debounce),clearTimeout]:[requestAnimationFrame(r),cancelAnimationFrame];n=()=>{d(m),n=null}}}const{proxy:f}=P();return T(()=>f.$q.lang.rtl,r),v(()=>{s=f.$el.parentNode,a()}),w(()=>{n?.(),l()}),Object.assign(f,{trigger:c,getPosition:()=>t}),L}});function N(){const e=Q(!k.value);return e.value===!1&&v(()=>{e.value=!0}),{isHydrated:e}}const M=typeof ResizeObserver<"u",E=M===!0?{}:{style:"display:block;position:absolute;top:0;left:0;right:0;bottom:0;height:100%;width:100%;overflow:hidden;pointer-events:none;z-index:-1;",url:"about:blank"},U=O({name:"QResizeObserver",props:{debounce:{type:[String,Number],default:100}},emits:["resize"],setup(e,{emit:o}){let t=null,n,i={width:-1,height:-1};function s(l){l===!0||e.debounce===0||e.debounce==="0"?r():t===null&&(t=setTimeout(r,e.debounce))}function r(){if(t!==null&&(clearTimeout(t),t=null),n){const{offsetWidth:l,offsetHeight:c}=n;(l!==i.width||c!==i.height)&&(i={width:l,height:c},o("resize",i))}}const{proxy:a}=P();if(a.trigger=s,M===!0){let l;const c=f=>{n=a.$el.parentNode,n?(l=new ResizeObserver(s),l.observe(n),r()):f!==!0&&x(()=>{c(!0)})};return v(()=>{c()}),w(()=>{t!==null&&clearTimeout(t),l!==void 0&&(l.disconnect!==void 0?l.disconnect():n&&l.unobserve(n))}),L}else{let l=function(){t!==null&&(clearTimeout(t),t=null),u!==void 0&&(u.removeEventListener!==void 0&&u.removeEventListener("resize",s,g.passive),u=void 0)},c=function(){l(),n?.contentDocument&&(u=n.contentDocument.defaultView,u.addEventListener("resize",s,g.passive),r())};const{isHydrated:f}=N();let u;return v(()=>{x(()=>{n=a.$el,n&&c()})}),w(l),()=>{if(f.value===!0)return R("object",{class:"q--avoid-card-border",style:E.style,tabindex:-1,type:"text/html",data:E.url,"aria-hidden":"true",onLoad:c})}}}}),G=(e,o)=>{const t=e.__vccOpts||e;for(const[n,i]of o)t[n]=i;return t};export{I as Q,G as _,U as a,j as b,B as g,$ as s};
