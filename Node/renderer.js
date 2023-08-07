const GopherClient = require('./gopherClient.js');

window.addEventListener('DOMContentLoaded', () => {
  const gc = new GopherClient('localhost', 10070);
  gc.start();
});
