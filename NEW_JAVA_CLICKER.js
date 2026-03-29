// NEW: Click ALL Java <a><span>Java</span></a> in app-code-tabs (scrolls page)
clickAllJavaTabs: function() {
  var clicked = 0;
  // Scroll to bottom first to render all tabs
  window.scrollTo(0, document.body.scrollHeight);

  var javaLinks = document.querySelectorAll('app-code-tabs a span');
  for (var i = 0; i < javaLinks.length; i++) {
    if (javaLinks[i].innerText.trim() === 'Java') {
      javaLinks[i].closest('a').click();
      clicked++;
      // Tiny sync delay
      var start = Date.now();
      while (Date.now() - start < 50) {}
    }
  }
  return clicked;
}