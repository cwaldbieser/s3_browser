
var $ = require( "jquery" );

// import { S3Client, GetObjectCommand } from "@aws-sdk/client-s3"; // ES Modules import
const { S3Client, GetObjectCommand } = require("@aws-sdk/client-s3"); // CommonJS import

const streamSaver = require('streamsaver')

async function downloadFromS3(bucketName, key, credentials) {
  const parts = key.split("/")
  const filename = parts[parts.length - 1]
  // StreamSaver can detect and use the Ponyfill that is loaded from the cdn.
  streamSaver.WritableStream = streamSaver.WritableStream

  // Initialize the Amazon Cognito credentials provider
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

function setEventHandlers() {
  $("a[data-key]").click(async function(){
    var key = $( this ).data("key");
    var bucketName = $("#bucket").data("bucket");
    await downloadFromS3(bucketName, key, credentials);
  });
}
$(document).ready(function(){
  configureApp();
  streamSaver.mitm = window.mitm;
  setEventHandlers();
});
