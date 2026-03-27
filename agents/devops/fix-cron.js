const fs = require('fs');
const file = '/home/axis/.openclaw/cron/jobs.json';
let data = JSON.parse(fs.readFileSync(file, 'utf8'));
let job = data.jobs.find(j => j.id === "4818c740-9125-43da-8778-3b540fbeaa76");
if (job && job.payload && job.payload.message) {
    job.payload.message = job.payload.message.replace(
        '/home/axis/openclaw/agents/tech/sessions/', 
        '/home/axis/.openclaw/agents/tech/sessions/'
    );
    fs.writeFileSync(file, JSON.stringify(data, null, 2));
    console.log("Fixed path in Job 4");
}
