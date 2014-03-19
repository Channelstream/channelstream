var state = {
    webapp_url : null,
    server_url : null,
    conn_id : null,
    socket : null,
    connection_request : null,
    on_connect_callback : null,
    reconnect_timout : null,
    heartbeat : null
};

// form submit event
$('#msg_form').submit(function() {
    var form_array = $(this).serializeArray();
    var post = {};
    for ( var int = 0; int < form_array.length; int++) {
        post[form_array[int].name] = form_array[int].value;
    }
    $('input[name=message]',this)[0].value = '';
    $.ajax({
        url : $(this).attr("action"),
        type : "POST",
        contentType : "application/json",
        data : JSON.stringify(post),
        dataType : "json",
    }).done(function() {

    });
    return false;
});

var messages_node = $('.messages')[0]
var got_message = function(entry) {
    $(messages_node).append(
    '<li><strong>channel:' + entry.channel + '</strong> <strong>' + entry.user
    + '</strong> <em>' + entry.message + '</em></li>');
}

var create_socket = function() {
    console.log('attempting to create socket');
    var socket_url = state.server_url + "/ws?conn_id=" + state.conn_id;
    var socket_conf = {
        url : socket_url,
        handleAs : 'json',
        headers : {
            "Accept" : "application/json",
            "Content-Type" : "application/json"
        }
    }
    socket_conf.url = socket_conf.url.replace('https', 'ws');
    socket_conf.url = socket_conf.url.replace('http', 'ws');
    state.socket = new WebSocket(socket_conf.url);

    state.socket.onopen = function(event) {
        console.log('open');
        setInterval(function(){
            console.log('heartbeat');
            state.socket.send('heartbeat')
        }, 10000)
    };
    state.socket.onmessage = function(event) {
        var data = $.parseJSON(event.data);
        for ( var i = 0; i < data.length; i++) {
            console.log('publishing: ' + 'gevent_cometd/' + data[i].type);
            got_message(data[i]);
        }
    };
    state.socket.onclose = function(event) {
        console.log('closed');
    };

    state.socket.onerror = function(event) {
        console.log('error');
    };


}

var get_conn_id = function(create_new_socket) {
    $.ajax({
        url : state.webapp_url + "/connect",
        type : "POST",
        contentType : "application/json",
        data : JSON.stringify(state.connection_request),
        dataType : "json",
    }).done(function(data) {
        console.log('Got connection:', data.conn_id)
        state.conn_id = data.conn_id;
        if (create_new_socket) {
            create_socket();
        }
    });
}

var demo_start = function(webapp_url, server_url, connection_request) {
    console.log('demo start');
    console.log('connecting to get UID of connection');
    state.connection_request = connection_request;
    state.webapp_url = webapp_url;
    state.server_url = server_url;
    state.on_connect_callback = null;
    get_conn_id(true);

}
