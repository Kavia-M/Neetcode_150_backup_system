window.__nc = {

  clickTab: function(tabName) {
    var tabs = document.querySelectorAll("[role='tab']");
    for (var i = 0; i < tabs.length; i++) {
      if (tabs[i].innerText.trim().toLowerCase().indexOf(tabName.toLowerCase()) > -1) {
        tabs[i].click();
        return "clicked tab: " + tabs[i].innerText.trim();
      }
    }
    return "tab not found";
  },

  expandAllAccordions: function() {
    var buttons = document.querySelectorAll("button");
    for (var i = 0; i < buttons.length; i++) {
      var text = buttons[i].innerText.trim();
      if (
        text.startsWith("Hint") ||
        text === "Topics" ||
        text.startsWith("Recommended Time")
      ) {
        buttons[i].click();
      }
    }
    // Also open any <details> elements (used on question pages)
    var details = document.querySelectorAll("details");
    for (var i = 0; i < details.length; i++) {
      details[i].setAttribute("open", "");
    }
    return true;
  },

  getSolutionText: function() {
      var article = document.querySelectorAll("app-article")[1] || document.querySelector("app-article");
      if (!article) return "";

      var elements = Array.from(article.querySelectorAll(
          "h1, h2, h3, h4, h5, h6, p:not([class*='step-description']), pre, ol, ul:not([class*='tabs-list']), math"
      ));

      // Keep only outermost matched elements
      var filtered = elements.filter(function(el) {
          return !elements.some(function(ancestor) {
              return ancestor !== el && ancestor.contains(el);
          });
      });

      function stripMath(el) {
          var clone = el.cloneNode(true);
          clone.querySelectorAll('math').forEach(function(m) { m.parentNode.removeChild(m); });
          return clone.innerText.trim();
      }

      function renderList(el, depth) {
          var result = "";
          var isOrdered = el.tagName === "OL";
          var counter = 1;
          var children = Array.from(el.children);
          for (var i = 0; i < children.length; i++) {
              var child = children[i];
              if (child.tagName !== "LI") continue;
              var indent = "  ".repeat(depth);
              // get direct text of this li (not nested lists, not math)
              var directText = Array.from(child.childNodes)
                  .filter(function(n) { return !(n.nodeType === 1 && (n.tagName === "OL" || n.tagName === "UL" || n.tagName === "MATH")); })
                  .map(function(n) {
                      if (n.nodeType === 1 && n.querySelector && n.querySelector('math')) {
                          var c = n.cloneNode(true);
                          c.querySelectorAll('math').forEach(function(m) { m.parentNode.removeChild(m); });
                          return c.textContent;
                      }
                      return n.textContent;
                  })
                  .join("").trim();
              // skip blank li — do not increment counter
              if (!directText) {
                  var nested = Array.from(child.children).filter(function(n) { return n.tagName === "OL" || n.tagName === "UL"; });
                  for (var j = 0; j < nested.length; j++) result += renderList(nested[j], depth + 1);
                  continue;
              }
              var bullet = isOrdered ? (counter++ + ".") : "-";
              result += indent + bullet + " " + directText + "\n";
              // recurse into nested lists
              var nested = Array.from(child.children).filter(function(n) { return n.tagName === "OL" || n.tagName === "UL"; });
              for (var j = 0; j < nested.length; j++) result += renderList(nested[j], depth + 1);
          }
          return result;
      }

      var HEADING_MAP = { H1: "##", H2: "###", H3: "####", H4: "#####", H5: "#####" };

      var text = "";
      for (var i = 0; i < filtered.length; i++) {
          var el = filtered[i];
          var tag = el.tagName;

          if (tag === "PRE") {
              var preText = el.innerText.trim();
              if (preText) text += "```\n" + preText + "\n```\n\n";
              continue;
          }
          if (tag === "MATH") {
              // standalone math — skip entirely (handled inline in p)
              continue;
          }
          if (tag === "OL" || tag === "UL") {
              var listText = renderList(el, 0).trim();
              if (listText) text += listText + "\n\n";
              continue;
          }
          if (HEADING_MAP[tag]) {
              var t = el.innerText.trim();
              if (t) text += HEADING_MAP[tag] + " " + t + "\n\n";
              continue;
          }
          if (tag === "H6") {
              var t = el.innerText.trim();
              if (t) text += "**" + t + "**\n\n";
              continue;
          }
          // p and everything else — strip all math elements, keep plain text
          var t = el.querySelectorAll('math').length > 0 ? stripMath(el) : el.innerText.trim();
          if (t) text += t + "\n\n";
      }
      return text;
  },

  getConstraints: function() {
    var strongs = document.querySelectorAll("strong");
    for (var i = 0; i < strongs.length; i++) {
      if (strongs[i].innerText.trim() === "Constraints:") {
        var ul = strongs[i].closest("p").nextElementSibling;
        if (ul && ul.tagName === "UL")
          return Array.from(ul.querySelectorAll("li")).map(function(li) { return li.innerText.trim(); });
      }
    }
    return [];
  },

  getJavaCode: function() {
    var lines = document.querySelectorAll(".cm-line");
    return Array.from(lines).map(function(l) { return l.innerText; }).join("\n");
  },

  clickJavaButton: function() {
    var buttons = document.querySelectorAll("button");
    for (var i = 0; i < buttons.length; i++) {
      if (buttons[i].innerText.trim() === "Java") {
        buttons[i].click();
        return true;
      }
    }
    return false;
  },
  
  // Click Java tab inside a specific code editor (by index)
  clickJavaInEditor: function(editorIndex) {
    var editors = document.querySelectorAll("app-solution-code-editor, .code-editor-container, [class*='code-editor']");
    if (editorIndex >= editors.length) return false;
    var editor = editors[editorIndex];
    var buttons = editor.querySelectorAll("button");
    for (var i = 0; i < buttons.length; i++) {
      if (buttons[i].innerText.trim() === "Java") {
        buttons[i].click();
        return true;
      }
    }
    return false;
  },

  // Count how many code editors exist on the page
  getCodeEditorCount: function() {
    var editors = document.querySelectorAll("app-solution-code-editor, .code-editor-container, [class*='code-editor']");
    return editors.length;
  },

  // Get Java code from a specific code editor (by index)
  getJavaFromEditor: function(editorIndex) {
    var editors = document.querySelectorAll("app-solution-code-editor, .code-editor-container, [class*='code-editor']");
    if (editorIndex >= editors.length) return "";
    var editor = editors[editorIndex];
    var lines = editor.querySelectorAll(".cm-line");
    return Array.from(lines).map(function(l) { return l.innerText; }).join("\n");
  },

  // Walk the solution content in DOM order — returns array of {type, content}
  // type = "text" or "code_index" (index into code editors list)
  getSolutionBlocks: function() {
    // Find the main solution content container
    var container = document.querySelector("app-solution-body, [class*='solution-body'], [class*='solution-content']");
    if (!container) {
      // fallback: use the main content area
      container = document.querySelector("main, .main-content, app-root");
    }
    if (!container) return [];

    var blocks = [];
    var editorIndex = 0;
    var children = container.childNodes;

    function walkNode(node) {
      if (node.nodeType === 3) { // text node
        var t = node.textContent.trim();
        if (t.length > 0) blocks.push({type: "text", content: t});
        return;
      }
      if (node.nodeType !== 1) return;
      var tag = node.tagName;

      // Skip video/canvas/iframe
      if (tag === "VIDEO" || tag === "CANVAS" || tag === "IFRAME") return;

      // Check if this is a code editor component
      var cn = (typeof node.className === "string") ? node.className : "";
      var isEditor = (
        tag === "APP-SOLUTION-CODE-EDITOR" ||
        cn.indexOf("code-editor") > -1
      );
      if (isEditor) {
        blocks.push({type: "code_index", content: String(editorIndex)});
        editorIndex++;
        return;
      }

      // For text-bearing elements, grab innerText
      if (tag === "P" || tag === "H1" || tag === "H2" || tag === "H3" || tag === "H4" || tag === "LI") {
        var text = (node.innerText || "").trim();
        if (text.length > 0) blocks.push({type: "text", content: text});
        return;
      }

      // recurse into children
      for (var i = 0; i < node.childNodes.length; i++) {
        walkNode(node.childNodes[i]);
      }
    }

    for (var i = 0; i < children.length; i++) {
      walkNode(children[i]);
    }
    return blocks;
  },

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
  },

  getSubmissionData: function() {
    var LANG_MAP = {
      'language-java':       'java',
      'language-javascript': 'javascript',
      'language-python':     'python',
      'language-cpp':        'cpp',
      'language-csharp':     'csharp',
      'language-go':         'go',
      'language-kotlin':     'kotlin',
      'language-swift':      'swift',
      'language-rust':       'rust'
    };

    // Status — check submission-status-row for "Accepted"
    var statusRow = document.querySelector('.submission-status-row');
    var accepted = false;
    if (statusRow) {
      var h1 = statusRow.querySelector('h1');
      if (h1) {
        accepted = h1.innerText.trim() === 'Accepted';
      } else {
        accepted = statusRow.innerText.indexOf('Accepted') > -1;
      }
    }
    var status = accepted ? 'correct' : 'wrong';

    // Code — find submission-code-block, then nested <code> with language class
    var codeBlock = document.querySelector('.submission-code-block');
    var code = '';
    var lang = 'unknown';
    if (codeBlock) {
      var codeEl = codeBlock.querySelector('code[class]');
      if (codeEl) {
        var classes = Array.from(codeEl.classList);
        for (var i = 0; i < classes.length; i++) {
          if (LANG_MAP[classes[i]]) {
            lang = LANG_MAP[classes[i]];
            break;
          }
        }
        code = codeEl.innerText;
      }
    }

    return { status: status, lang: lang, code: code };
  }
};
