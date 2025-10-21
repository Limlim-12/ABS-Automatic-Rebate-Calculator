module.exports = {
  // These are the files PurgeCSS will scan for CSS classes
  content: [
    './templates/index.html', //
    './templates/result.html', //
    './templates/admin.html',
    './templates/history.html',
    './templates/subscriber_form.html'
  ],

  // This is your CSS file that it will clean
  css: [
    './static/style.css' //
  ],

  // This is where it will save the new, small, "purged" file
  output: './static/style.min.css'
};