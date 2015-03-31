'use strict';

angular.module('adagios.tactical.status_overview', ['ngRoute' ])

    .controller('TacticalStatusOverViewCtrl', ['$scope', function ($scope) {
        $scope.hosts = {
            "count": 104,
            "problems": 14
        };

        $scope.services = {
            "count": 1126,
            "problems": 42
        };
    }])

    .directive('adgStatusOverview', function () {
        return {
            restrict: 'E',
            templateUrl: 'components/tactical/status_overview/status_overview.html'
        };
    });
