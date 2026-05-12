const rawContentNode = document.getElementById("raw-content");
const contentNode = document.getElementById("content");
const copyRichButton = document.getElementById("copy-rich");
const copyMarkdownButton = document.getElementById("copy-md");
const statusNode = document.getElementById("status");

let rawContent = "";

if (rawContentNode?.textContent) {
  try {
    rawContent = JSON.parse(rawContentNode.textContent);
  } catch {
    rawContent = "";
  }
}

function setStatus(message) {
  if (!statusNode) return;
  statusNode.textContent = message;
  setTimeout(() => {
    if (statusNode.textContent === message) statusNode.textContent = "";
  }, 2000);
}

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function wrapToken(type, value) {
  return `<span class="token ${type}">${escapeHtml(value)}</span>`;
}

function replacePlainSegments(text, pattern, replacer) {
  const parts = text.split(/(<span class="token [^"]+">.*?<\/span>)/gs);
  return parts
    .map((part) => (part.startsWith("<span ") ? part : part.replace(pattern, replacer)))
    .join("");
}

function highlightYaml(text) {
  const lines = text.split("\n");
  return lines
    .map((line) => {
      const commentMatch = line.match(/^(\s*#.*)$/);
      if (commentMatch) {
        return wrapToken("comment", line);
      }

      const keyMatch = line.match(/^(\s*-\s+)?([A-Za-z0-9_."'\/-]+)(\s*:\s*)(.*)$/);
      if (!keyMatch) {
        return escapeHtml(line).replace(
          /\b(true|false|null|yes|no|on|off)\b|\b\d+(?:\.\d+)?\b/g,
          '<span class="token literal">$&</span>',
        );
      }

      const [, listPrefix = "", key, separator, rest] = keyMatch;
      const value = escapeHtml(rest).replace(
        /\b(true|false|null|yes|no|on|off)\b|\b\d+(?:\.\d+)?\b/g,
        '<span class="token literal">$&</span>',
      );
      return `${escapeHtml(listPrefix)}<span class="token property">${escapeHtml(key)}</span>${escapeHtml(separator)}${value}`;
    })
    .join("\n");
}

function readQuoted(text, start, quote) {
  let index = start + 1;
  while (index < text.length) {
    if (text[index] === "\\") {
      index += 2;
      continue;
    }
    if (quote !== "```" && text[index] === quote) {
      return { value: text.slice(start, index + 1), end: index + 1 };
    }
    if (
      quote === "```" &&
      text[index] === "`" &&
      text[index + 1] === "`" &&
      text[index + 2] === "`"
    ) {
      return { value: text.slice(start, index + 3), end: index + 3 };
    }
    index += 1;
  }
  return { value: text.slice(start), end: text.length };
}

function highlightStructuredCode(text, options) {
  const { commentStart, keywords, builtins = [] } = options;
  let result = "";
  let index = 0;

  while (index < text.length) {
    if (commentStart && text.startsWith(commentStart, index)) {
      let end = text.indexOf("\n", index);
      if (end === -1) end = text.length;
      result += wrapToken("comment", text.slice(index, end));
      index = end;
      continue;
    }

    const char = text[index];
    if (char === '"' || char === "'") {
      const token = readQuoted(text, index, char);
      result += wrapToken("string", token.value);
      index = token.end;
      continue;
    }

    if (char === "`") {
      const token = readQuoted(text, index, "```");
      result += wrapToken("string", token.value);
      index = token.end;
      continue;
    }

    result += escapeHtml(char);
    index += 1;
  }

  result = replacePlainSegments(
    result,
    /\b(true|false|null|undefined|None|True|False)\b|\b\d+(?:\.\d+)?\b/g,
    '<span class="token literal">$&</span>',
  );
  result = replacePlainSegments(
    result,
    new RegExp(`\\b(${keywords.join("|")})\\b`, "g"),
    '<span class="token keyword">$1</span>',
  );

  if (builtins.length) {
    result = replacePlainSegments(
      result,
      new RegExp(`\\b(${builtins.join("|")})\\b`, "g"),
      '<span class="token builtin">$1</span>',
    );
  }

  return result;
}

function highlightPython(text) {
  return highlightStructuredCode(text, {
    commentStart: "#",
    keywords: [
      "def",
      "class",
      "return",
      "if",
      "elif",
      "else",
      "for",
      "while",
      "try",
      "except",
      "finally",
      "with",
      "as",
      "import",
      "from",
      "pass",
      "break",
      "continue",
      "yield",
      "lambda",
      "async",
      "await",
      "match",
      "case",
    ],
    builtins: ["self"],
  });
}

function highlightJson(text) {
  let result = escapeHtml(text);
  result = replacePlainSegments(
    result,
    /&quot;([^"\\]|\\.)*&quot;/g,
    '<span class="token string">$&</span>',
  );
  result = result.replace(
    /<span class="token string">(&quot;(?:[^"\\]|\\.)*&quot;)<\/span>(\s*:)/g,
    '<span class="token property">$1</span>$2',
  );
  result = replacePlainSegments(
    result,
    /\b(true|false|null)\b|\b-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?\b/g,
    '<span class="token literal">$&</span>',
  );
  return result;
}

function highlightTypeScript(text) {
  return highlightStructuredCode(text, {
    commentStart: "//",
    keywords: [
      "import",
      "from",
      "export",
      "default",
      "const",
      "let",
      "var",
      "function",
      "return",
      "if",
      "else",
      "for",
      "while",
      "switch",
      "case",
      "break",
      "continue",
      "try",
      "catch",
      "finally",
      "throw",
      "new",
      "class",
      "extends",
      "implements",
      "interface",
      "type",
      "enum",
      "as",
      "async",
      "await",
      "typeof",
      "instanceof",
    ],
  });
}

function highlightCodeBlocks() {
  const nodes = document.querySelectorAll("pre code[data-language]");
  for (const node of nodes) {
    const language = node.dataset.language;
    const source = node.textContent ?? "";
    if (!source) continue;

    if (language === "yaml" || language === "yml") {
      node.innerHTML = highlightYaml(source);
      continue;
    }

    if (language === "python" || language === "py") {
      node.innerHTML = highlightPython(source);
      continue;
    }

    if (language === "json") {
      node.innerHTML = highlightJson(source);
      continue;
    }

    if (["typescript", "ts", "tsx", "javascript", "js", "jsx"].includes(language)) {
      node.innerHTML = highlightTypeScript(source);
    }
  }
}

async function copyRichText() {
  if (!contentNode || !navigator.clipboard || !window.ClipboardItem) return;
  const htmlBlob = new Blob([contentNode.innerHTML], { type: "text/html" });
  const textBlob = new Blob([contentNode.innerText], { type: "text/plain" });
  await navigator.clipboard.write([
    new ClipboardItem({ "text/html": htmlBlob, "text/plain": textBlob }),
  ]);
  setStatus("Copied");
}

async function copyMarkdown() {
  if (!navigator.clipboard) return;
  await navigator.clipboard.writeText(rawContent);
  setStatus("Copied");
}

highlightCodeBlocks();

if (copyRichButton) copyRichButton.addEventListener("click", copyRichText);
if (copyMarkdownButton) copyMarkdownButton.addEventListener("click", copyMarkdown);
