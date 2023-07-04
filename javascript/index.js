const grApp = gradioApp();

function clamp(num, min, max) {
  return Math.min(Math.max(num, min), max);
}

async function sendToControlNet(imgUrl, tabName, tabIndex) {
  const response = await fetch(imgUrl);
  const imageBlob = await response.blob();
  const imageFile = new File([imageBlob], "image.png", { type: "image/png" });
  const dataTransfer = new DataTransfer();
  dataTransfer.items.add(imageFile);
  const fileList = dataTransfer.files;

  window[`switch_to_${tabName}`]?.();

  const controlNetElement = grApp.querySelector(`#${tabName}_script_container #controlnet`);
  const accordionElement = controlNetElement.querySelector(":scope > .label-wrap");
  if (!accordionElement.classList.contains("open")) {
    accordionElement.click();
  }

  const tabsButton = controlNetElement.querySelectorAll("div.tab-nav > button");
  if (tabsButton !== null && tabsButton.length > 1) {
    tabsButton[tabIndex].click();
  }

  const fileInputs = controlNetElement.querySelectorAll("input[type='file']");
  let fileInput = fileInputs[tabIndex * 2];
  if (fileInput == null) {
    const callback = (observer) => {
      fileInput = controlNetElement.querySelector("input[type='file']");
      if (fileInput == null) {
        return;
      } else {
        setImage(fileInput, fileList);
        observer.disconnect();
      }
    };
    const observer = new MutationObserver(callback);
    observer.observe(controlNetElement, { childList: true });
  } else {
    setImage(fileInput, fileList);
  }
}

function setImage(input, fileList) {
  try {
    input.previousElementSibling?.previousElementSibling?.querySelector("button[aria-label='Clear']")?.click();
  } catch (e) {
    console.error(e);
  }
  input.value = '';
  input.files = fileList;
  const changeEvent = new Event('change', { bubbles: true, composed: true });
  input.dispatchEvent(changeEvent);
}