/*
 * Copyright (C) 2025  Dawid Zielinski
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; version 3.
 *
 * szaszki is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

import QtQuick 2.7
import Lomiri.Components 1.3
//import QtQuick.Controls 2.2
import QtQuick.Layouts 1.3
import Qt.labs.settings 1.0
import io.thp.pyotherside 1.4

MainView {
    id: root
    objectName: 'mainView'
    applicationName: 'szaszki.dywan1na'
    automaticOrientation: true

    width: units.gu(45)
    height: units.gu(75)

    Page {
        anchors.fill: parent

        header: PageHeader {
            id: header
            title: i18n.tr('szaszki!chess!')
        }

        Label {
            anchors {
                top: header.bottom
                left: parent.left
                right: parent.right
                bottom: parent.bottom
            }
            text: i18n.tr('Check the logs!')

            verticalAlignment: Label.AlignVCenter
            horizontalAlignment: Label.AlignHCenter
        }
    }

    Python {
        id: python

        Component.onCompleted: {
            addImportPath(Qt.resolvedUrl('../src/'));

            importModule('example', function() {
                console.log('module imported');
                python.call('example.speak', ['Hello World!'], function(returnValue) {
                    console.log('example.speak returned ' + returnValue);
                })
            });
        }

        onError: {
            console.log('python error: ' + traceback);
        }
    }
}
