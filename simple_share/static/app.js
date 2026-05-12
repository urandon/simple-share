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

if (copyRichButton) copyRichButton.addEventListener("click", copyRichText);
if (copyMarkdownButton) copyMarkdownButton.addEventListener("click", copyMarkdown);
