// toggle "Accessibility Options" menu
const showAccessibilityMenu = () => {
  const fontSelection = document.getElementById("font-selection");
  if (fontSelection.classList.contains("display-none")) {
    fontSelection.classList.remove("display-none");
  } else {
    fontSelection.classList.add("display-none");
  }
  const backgroundSelection = document.getElementById("background-selection");
  if (backgroundSelection.classList.contains("display-none")) {
    backgroundSelection.classList.remove("display-none");
  } else {
    backgroundSelection.classList.add("display-none");
  }
};

// set font
const changeFont = event => {
  console.log("You selected: ", event.target.value);
  const font = event.target.value;
  const contentNode = document.getElementsByClassName("fontchange")[0];
  contentNode.classList.remove(
    "font-SylexiadSans",
    "font-AtkinsonHyperlegible",
    "font-OpenDyslexicThree",
    "font-Ubuntu",
    "font-serif",
    "font-sans"
  );
  contentNode.classList.add(`font-${font}`);
  window.localStorage.setItem("font", font);
};

const changeBackground = event => {
  let show_grid = document.getElementById("background-grid").checked;
  let show_blobs = document.getElementById("background-blobs").checked;
  try{
      if(event.target.name == "background-grid"){
    show_grid = event.target.checked;
  }
  if(event.target.name == "background-blobs"){
    show_blobs = event.target.checked;
  }
  }catch{}
  const blobs = document.getElementsByClassName("blobs");
  if(show_blobs){
    for (let i = 0; i < blobs.length; i++) {
      blobs[i].classList.remove('display-none')
    }
  }else{
    for (let i = 0; i < blobs.length; i++) {
      blobs[i].classList.add('display-none')
    }
  }
  if(show_grid){
    document.body.classList.add('background-grid')
  }else{
    document.body.classList.remove('background-grid')
  }
  window.localStorage.setItem("background-grid", show_grid);
  window.localStorage.setItem("background-blobs", show_blobs);
};

// get settings from localStorage
window.onload = function() {
  let previousFont = localStorage.getItem("font");
  if(previousFont == null){
    previousFont = "Ubuntu"
  }
  const contentNode = document.getElementsByClassName("fontchange")[0];
  contentNode.classList.remove(
    "font-SylexiadSans",
    "font-AtkinsonHyperlegible",
    "font-OpenDyslexicThree",
    "font-Ubuntu",
    "font-serif",
    "font-sans"
  );
  contentNode.classList.add(`font-${previousFont}`);
  console.log("Previously selected font: ", previousFont);
  radiobtn = document.getElementById(`font-${previousFont}`);
  radiobtn.checked = true;
  let show_grid = localStorage.getItem("background-grid");
  let show_blobs = localStorage.getItem("background-blobs");
  if(show_grid == null){
    show_grid = true;
  }
  if(show_blobs == null){
    show_blobs = true;
  }
  document.getElementById("background-grid").checked = show_grid;
  document.getElementById("background-blobs").checked = show_blobs;
  changeBackground()
};

document
  .querySelector("#accessibility-options button")
  .addEventListener("click", showAccessibilityMenu);
document
  .getElementById("font-selection")
  .addEventListener("change", changeFont);
document
  .getElementById("background-selection")
  .addEventListener("change", changeBackground);

// no-js handling
for (let el of document.querySelectorAll(".no-js")) el.style.display = "none";
for (let el of document.querySelectorAll(".js")) el.style.display = "block";
