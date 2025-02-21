function printICOnly() {
  // Hide all content except images
  document.querySelector(".student-info").style.display = "none";
  document.querySelector("h1").style.display = "none";
  document.querySelector(".button-container").style.display = "none";

  // Ensure only images are visible
  document.querySelector(".student-photos").style.display = "block";

  window.print();

  // Restore visibility after printing
  document.querySelector(".student-info").style.display = "";
  document.querySelector("h1").style.display = "";
  document.querySelector(".button-container").style.display = "";
}
