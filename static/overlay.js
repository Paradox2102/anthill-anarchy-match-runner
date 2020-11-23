// When combining this overlay with video and audio streams, it is important to synchronize them.
// To support this, we read the URL parameter "delay" and we sleep for that long (in seconds) 
// before executing server events.  This allows the client to delay the browser overlay source.

const queryString = window.location.search;
const urlParams = new URLSearchParams(queryString);
const delay = urlParams.get('delay', 0);

$(document).ready(function() {
    namespace = '/overlay';
    var socket = io(namespace);

    // When we receive an "update_event" from the server, set the various small text elements.
    // Data contains id strings, which should be on DIVs containing Ps.
    socket.on('update_text', async function(data, cb) {
        // Sleep for "delay" seconds.
        if(delay > 0) { await new Promise(r => setTimeout(r, delay*1000)); }
        for(const property in data) {
            $("#" + property + " p").html(data[property]);
        }
        if(cb) { cb(); }
    });

    // When we receive the "show_table" event from the server, 
    // we display an arbitrary HTML fragment (probably a table).
    // The data is a raw HTML string or null.
    // If null, then the element is hidden.
    socket.on('show_table', async function(data, cb) {
        // Sleep for "delay" seconds.
        if(delay > 0) { await new Promise(r => setTimeout(r, delay*1000)); }
        if(data == null) {
            $("#table")[0].style.display = "none";
        } else {
            $("#table").html(data);
            $("#table")[0].style.display = "block";
        }
        if(cb) { cb(); }
    });

    // When we receive the "play_audio" event from the server,
    // we invoke the play() method on the element with the indicated id.
    // TODO: Support volume?
    socket.on('play_audio', async function(data, cb) {
        // Sleep for "delay" seconds.
        if(delay > 0) { await new Promise(r => setTimeout(r, delay*1000)); }
        var obj = $("audio#" + data)[0];
        //obj.volume = 0.1; // Doesn't seem to work.
        obj.play();
        if(cb) { cb(); }
    });                   
});
