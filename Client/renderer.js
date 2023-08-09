const GopherClient = require('./GopherClient.js');
const ViewController = require('./ViewController.js');

window.addEventListener('DOMContentLoaded', () => {
  console.log("Starting Gopher client...");
  const gc = new GopherClient('localhost', 10070);
  console.log("Initializing view...")
  const view = new ViewController(gc);
});
