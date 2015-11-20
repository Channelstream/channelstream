var channelstreamApp = angular.module('channelstreamApp', []);

channelstreamApp.controller('chatCtl', function ($scope, $http) {
    $scope.user = {
        username: 'user_' + Math.round(Math.random() * 10000)
    };
    $scope.channels = ['pub_chan', 'pub_chan2'];
    $scope.selected_channel = {value: $scope.channels[0]}
    $scope.stream = [];
    $scope.conn_id = null;
    $scope.websocket = null;

    var use_websocket = true;


    var webapp_url = window.location.toString();
    var ws_url = webapp_url.replace('/demo', '').replace('http://', 'ws://');
    var longpoll_url = webapp_url.replace('/demo', '').replace('http://', '//');

    $scope.subscribe_channel = function () {
        var json_data = {
            channels: ['notify'],
            conn_id: $scope.conn_id
        };
        $http({
            method: 'POST',
            url: webapp_url + '/subscribe',
            data: json_data
        }).
            success(function (data, status, headers, config) {
                $scope.channels = data;
            }).
            error(function (data, status, headers, config) {
                // called asynchronously if an error occurs
                // or server returns response with an error status.
            });
    }

    $scope.unsubscribe_channel = function () {
        var json_data = {
            channels: ['notify'],
            conn_id: $scope.conn_id
        };
        $http({
            method: 'POST',
            url: webapp_url + '/unsubscribe',
            data: json_data
        }).
            success(function (data, status, headers, config) {
                $scope.channels = data;
            }).
            error(function (data, status, headers, config) {
                // called asynchronously if an error occurs
                // or server returns response with an error status.
            });
    }

    $scope.send_message = function () {
        var json_data = {
            message: $scope.message,
            channel: $scope.selected_channel.value,
            user: $scope.user.username
        };
        $http({method: 'POST', url: webapp_url + '/message', data: json_data}).
            success(function (data, status, headers, config) {
                $scope.message = ''
            }).
            error(function (data, status, headers, config) {
                // called asynchronously if an error occurs
                // or server returns response with an error status.
            });
    }

    var on_message = function (data) {
        console.log('message');
        $scope.$apply(function (scope) {
            _.each(data, function (message) {
                if (scope.stream.length > 10) {
                    scope.stream.shift();
                }
                scope.stream.push(message);

            });
        });
    }
    var on_close = function (event) {
        console.log('closed');
        setTimeout(authorize, 5000);
    }
    var on_error = function () {
        console.log('error');
    }
    var on_open = function (event) {
        console.log('open');
    }
    var json_data = {
        'user': $scope.user.username,
        'channels': $scope.channels
    }

    var poll = function (url) {
        $http({
            method: 'GET',
            url: longpoll_url + '/listen?conn_id=' + $scope.conn_id
        }).
            success(function (data, status, headers, config) {
                console.log(data);
                setTimeout(function () {
                    on_message(data)
                }, 0);
                poll(url);
            }).
            error(function (data, status, headers, config) {
                on_close()
            });
    };

    var connect = function (use_websocket) {
        if (use_websocket) {
            var url = ws_url + '/ws?conn_id=' + $scope.conn_id;
            console.log(url);
            $scope.websocket = new WebSocket(url);
            $scope.websocket.onopen = on_open;
            $scope.websocket.onclose = on_close;
            $scope.websocket.onerror = on_error;
            $scope.websocket.onmessage = function (event) {
                on_message(JSON.parse(event.data));
            };
        }
        else {
            var url = longpoll_url + '/listen?conn_id=' + $scope.conn_id;
            console.log(url);
            poll(url);
        }
    }

    var authorize = function () {
        $http({method: 'POST', url: webapp_url + '/connect', data: json_data}).
            success(function (data, status, headers, config) {
                $scope.conn_id = data.conn_id;
                $scope.user.username = data.username;
                connect(use_websocket);
            }).
            error(function (data, status, headers, config) {
                // called asynchronously if an error occurs
                // or server returns response with an error status.
            });
    }

    authorize();

});
