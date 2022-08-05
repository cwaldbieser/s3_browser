
var $ = require( "jquery" );

// import { S3Client, GetObjectCommand } from "@aws-sdk/client-s3"; // ES Modules import
const { S3Client, GetObjectCommand, PutObjectCommand } = require("@aws-sdk/client-s3"); // CommonJS import

const streamSaver = require('streamsaver')

async function downloadFromS3(bucketName, key, credentials) {
  const parts = key.split("/")
  const filename = parts[parts.length - 1]
  // StreamSaver can detect and use the Ponyfill that is loaded from the cdn.
  streamSaver.WritableStream = streamSaver.WritableStream

  const REGION = "us-east-1"; //e.g., 'us-east-1'
  const config = {
    region: REGION,
    credentials: credentials}

  const s3 = new S3Client(config);
  const bucketParams = {
    Bucket: bucketName,
    Key: key,
  }

  const client = new S3Client(config);
  const command = new GetObjectCommand(bucketParams);
  async function getDownloadResponse(){
    try {
      return await client.send(command);
    }
    catch(error) {
      console.log(error);
      return null;
    }
  }
  const response = await getDownloadResponse();
  if(response == null){
    alert("Permission error downloading file.");
    return;
  }
  const contentType = response.Body.contentType

  // streamSaver.createWriteStream() returns a writable byte stream
  // The WritableStream only accepts Uint8Array chunks
  // (no other typed arrays, arrayBuffers or strings are allowed)
  const fileStream = streamSaver.createWriteStream(filename)
  const readableStream = response.Body

  // more optimized
  if (window.WritableStream && readableStream.pipeTo) {
    return readableStream.pipeTo(fileStream)
      .then(() => console.log('done writing'))
  }

  window.writer = fileStream.getWriter()

  const reader = response.body.getReader()
  const pump = () => reader.read()
    .then(res => res.done
      ? writer.close()
      : writer.write(res.value).then(pump))

  pump()
}

async function uploadFileHandler(bucketName) {
  var files = document.getElementById("fileupload").files;
  if (!files.length) {
    return alert("Please choose a file to upload first.");
  }
  var file = files[0];
  var fileName = file.name;
  var bucketPrefix = $("#upload-button").data("prefix");
  var fileKey = "";
  if(bucketPrefix != "") {
    fileKey = bucketPrefix + "/" + fileName;
  }
  else {
    fileKey = fileName;
  }

  const REGION = "us-east-1"; //e.g., 'us-east-1'
  const config = {
    region: REGION,
    credentials: credentials}

  const s3 = new S3Client(config);
  const uploadParams = {
    Bucket: bucketName,
    Key: fileKey,
    Body: file,
  }

  try {
    const data = await s3.send(new PutObjectCommand(uploadParams));
    alert("Successfully uploaded photo.");
    location.reload();
  }
  catch (err) {
    console.log(err)
    return alert("There was an error uploading your photo: ", err.message);
  }
}


function deleteFromS3(key) {
  var path = location.pathname;
  if(path != "" && !path.endsWith("/")) {
    path = path + "/";
  }
  path = path + key;
  var url = new URL(location);
  url.pathname = path;
  console.log(url);
  fetch(url, {
    method: "DELETE",
    credentials: 'same-origin',
    headers: {
      'X-CSRFToken': csrf_token,
    },
  }).then(function(data){
      if(data.status < 200 || data.status > 299) {
        console.log(data)
        alert("Could not delete object.");
      }
      else {
        location.reload();
      }
    },
    function(reason){
      alert("Could not delete object.");
      console.log("Failure: " + reason);
    }
  );
}


function setEventHandlers() {
  var bucketName = $("#bucket").data("bucket");
  $("a[data-btnType='download']").click(async function(){
    var key = $( this ).data("key");
    await downloadFromS3(bucketName, key, credentials);
  });
  $("#upload-button").click(function(){
    uploadFileHandler(bucketName);
  });
  $("a[data-btnType='delete']").click(async function(){
    var key = $( this ).data("key");
    await deleteFromS3(key);
  });
}
$(document).ready(function(){
  configureApp();
  streamSaver.mitm = window.mitm;
  setEventHandlers();
});
