var channelstreamApp = angular.module('channelstreamApp', []);

channelstreamApp.controller('chatCtl', function ($scope, $http) {
    $scope.user = {
        user_name: 'user_' + Math.round(Math.random() * 10000)
    };
    $scope.channels = ['pub_chan', 'pub_chan2'];
    $scope.selected_channel = {value: $scope.channels[0]}
    $scope.stream = [];
    $scope.conn_id = null;
    $scope.websocket = null;

    var webapp_url = window.location.toString();
    var server_url = webapp_url.replace('/demo', '/ws').replace('http://', 'ws://');

    $scope.subscribe_channel = function () {
        var json_data = {
            channels: ['notify'],
            conn_id: $scope.conn_id };
        $http({method: 'POST', url: webapp_url + '/subscribe', data: json_data}).
            success(function (data, status, headers, config) {
                $scope.channels = data;
            }).
            error(function (data, status, headers, config) {
                // called asynchronously if an error occurs
                // or server returns response with an error status.
            });
    }

    $scope.send_message = function () {
        var json_data = {message: $scope.message,
            channel: $scope.selected_channel.value,
            user: $scope.user.user_name };
        $http({method: 'POST', url: webapp_url + '/message', data: json_data}).
            success(function (data, status, headers, config) {
                $scope.message = ''
            }).
            error(function (data, status, headers, config) {
                // called asynchronously if an error occurs
                // or server returns response with an error status.
            });
    }

    var json_data = {'user': $scope.user.user_name,
        'channels': $scope.channels
    }

    $http({method: 'POST', url: webapp_url + '/connect', data: json_data}).
        success(function (data, status, headers, config) {
            console.log(data);
            $scope.conn_id = data.conn_id;
            console.log(server_url + '/ws?conn_id=' + $scope.conn_id)
            $scope.websocket = new WebSocket(server_url + '/ws?conn_id=' + $scope.conn_id);
            $scope.websocket.onopen = function (event) {
                console.log('open');
            };
            $scope.websocket.onmessage = function (event) {
                var data = JSON.parse(event.data);
                console.log('message');
                $scope.$apply(function (scope) {
                    _.each(data, function (message) {
                        if (scope.stream.length > 10) {
                            scope.stream.shift();
                        }
                        scope.stream.push(message);

                    });
                });
            };
            $scope.websocket.onclose = function (event) {
                console.log('closed');
            };

            $scope.websocket.onerror = function (event) {
                console.log('error');
            };
        }).
        error(function (data, status, headers, config) {
            // called asynchronously if an error occurs
            // or server returns response with an error status.
        });


});