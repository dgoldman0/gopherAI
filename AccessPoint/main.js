const express = require('express');
const bodyParser = require('body-parser');
const rateLimit = require('express-rate-limit');
const path = require('path'); 
const { rejects } = require('assert');
const { GopherClient } = require(path.join(__dirname, '../Browser/Gopher.js'));

const app = express();

app.use(bodyParser.urlencoded({ extended: false }));

// Setup rate limiter
const limiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 100,                 // limit each IP to 100 requests per windowMs
    message: "Too many requests from this IP, please try again after 15 minutes."
});

// Apply rate limiter to the /query route
app.use('/query', limiter);

const gopherClient = new GopherClient('localhost', 10070);

// Serve a basic HTML form at the root
app.get('/', (req, res) => {
    res.send(`
        <form action="/query" method="post">
            <input type="text" name="query" placeholder="Enter your query">
            <button type="submit">Submit</button>
        </form>
    `);
});

// Handle the form submission
app.post('/query', async (req, res) => {
    const userQuery = req.body.query;

    try {
        // Use your GopherClient to query
        const result = await gopherClient.query('inquiry', "*INQUIRY:" + userQuery, true);  // or query method when implemented
        console.log("Result:" + result.toString());
        res.send(result);
    } catch (err) {
        console.log(err);
        res.send(err);
    }
});

app.listen(3000, () => {
    console.log('Server listening on port 3000');
});
