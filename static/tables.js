
$(document).ready(function(){
  $("#filesTable").DataTable();
  $("#filesTable").on("search.dt", S3BLibrary.setFileEventHandlers);
});

