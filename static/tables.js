
$(document).ready(function(){
  $("#filesTable").DataTable();
  $("#filesTable").on("search.dt", function () {
    window.setTimeout(S3BLibrary.setFileEventHandlers, 500);
  }).on("page.dt", function () {
    window.setTimeout(S3BLibrary.setFileEventHandlers, 500);
  }).on("length.dt", function () {
    window.setTimeout(S3BLibrary.setFileEventHandlers, 500);
  });
  $("#foldersTable").DataTable();
});

