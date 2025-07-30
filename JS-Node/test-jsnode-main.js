const express = require('express');
const { exec } = require('child_process');
const app = express();

app.get('/ping', (req, res) => {
    const host = req.query.host;
    exec(`ping -c 4 ${host}`, (error, stdout, stderr) => {
        if (error) {
            res.send(`Error: ${stderr}`);
        } else {
            res.send(`<pre>${stdout}</pre>`);
        }
    });
});

app.listen(3000, () => console.log('Server running on port 3000'));
