$(document).ready(function() {
    namespace = '/control';
    var socket = io(namespace);

    // When the user clicks on a button, send the associated event to the server.
    function handle_button_click(event, data) {
        socket.emit(data['event'], data['arg']);
        //console.log("handle_button_click: " + data);
    }

    // When the server sends a "set_buttons" event, create HTML buttons, optionally clearing the list.
    // Data is an object with fields:
    //     clear: If true, delete all existing buttons
    //     buttons: Array of objects with fields like:
    //         event: Event string to send to server on click
    //         arg: Argument to send to server
    //         label: String to show to user.
    socket.on('set_buttons', function(data, cb) {
        //console.log("set_buttons: data=" + data);
        var buttons = $("div#buttons");     
        //console.log("buttons=" + buttons);
        if(data['clear']) {
            buttons.empty();
        }
        data['buttons'].forEach(function (item, index) {
            var button = document.createElement("button");
            button.innerHTML = item["label"];
            //console.log("Button: " + item["label"]);
            button.addEventListener("click", function(event) { handle_button_click(event, item); });
            buttons.append(button);
        });
        if(cb) { cb(); }
    });

    // When the server sends a "log_message" event, send the argument to console and print on-screen with a timestamp.
    socket.on('log_message', function(data, cb) {
        var log = $("#log");
        var now = new Date().toISOString();
        console.log(now + " " + data);
        log.prepend(document.createElement("br"));
        log.prepend(document.createTextNode(now + " " + data));
    });                    
});
$(iframe)[0].mute();
