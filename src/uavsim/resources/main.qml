import QtQuick 2.9
import QtQuick.Window 2.11
import QtGraphicalEffects 1.0
import QtLocation 5.11
import QtPositioning 5.11
import QtQuick.Controls 2.4
import QtQuick.Layouts 1.3


ApplicationWindow {
    id: appWin
    property real heading: 0
    property var jetPos: QtPositioning.coordinate(0.00, 0.00)
    property var wind: {
        direction: null
        speed: 0
    }

    width: 1000
    height: 630
    visible: true

    Plugin {
        id: osmPlugin
        name: "osm"
    }

    RowLayout {
        anchors.fill: parent

        ColumnLayout {
            Map {
                id: map
                anchors.fill: parent
                copyrightsVisible: false
                plugin: osmPlugin
                center: QtPositioning.coordinate(56.88614457563706, 24.20416950429917)
                activeMapType: supportedMapTypes[MapType.TerrainMap]
                zoomLevel: 10

                MapQuickItem {
                    id: marker
                    objectName: "marker"
                    transform: Rotation { origin.x: jetIcon.width / 2; origin.y: jetIcon.height / 2; angle: appWin.heading}

                    sourceItem: Item {
                        Image {
                            id: jetIcon
                            anchors.centerIn: parent.Center
                            source: "images/jet.png"
                        }

                        ColorOverlay {
                            anchors.fill: jetIcon
                            anchors.centerIn: parent.Center
                            source: jetIcon
                            color: "#AAFF0000"
                        }
                    }

                    coordinate: appWin.jetPos
                    anchorPoint.x: jetIcon.width / 2
                    anchorPoint.y: jetIcon.height / 2
                }

                onZoomLevelChanged: {
                    marker.coordinate = appWin.jetPos
                }

                onCenterChanged: {
                    marker.coordinate = appWin.jetPos
                }

                MouseArea {
                    property var forcePos

                    anchors.fill: parent
                    acceptedButtons: Qt.LeftButton | Qt.RightButton
                    onPressed: {
                        if (mouse.button & Qt.RightButton) {
                        } else if (mouse.button & Qt.LeftButton) {
                            forcePos = map.toCoordinate(Qt.point(mouse.x, mouse.y))
                            locator.forceLocation(forcePos.latitude.toString(), forcePos.longitude.toString())
                        }
                    }
                }
            }

//            Column {
//                id: textColumn
//                width: 200
//                height: 400
//
//                Text {
//                    id: posLatitudeText
//                    text: qsTr("Latitude: " + jetPos.latitude.toString())
//                    font.pixelSize: 12
//                }
//
//                Text {
//                    id: posLongitudeText
//                    text: qsTr("Longitude: " + jetPos.longitude.toString())
//                    font.pixelSize: 12
//                }
//            }
        }
        ColumnLayout {
            Rectangle {
                color: "plum"
                Layout.minimumWidth: 200
                Layout.preferredWidth: 200
                Layout.fillHeight: true
                Text {
                    anchors.centerIn: parent
                    text: parent.width + "x" + parent.height
                }
            }
            Label {
                text: "PID settings"
            }
            Label {
                text: "kP"
            }
            SpinBox {
                id: pid_kp
                editable: true
                from: 0
                to: 100000

                property int decimals: 5
                property real realValue: value / 100000

                textFromValue: function(value, locale) {
                    return Number(value / 100000).toLocaleString(locale, "f", pid_kp.decimals)
                }

                valueFromText: function(text, locale) {
                    return Number.fromLocaleString(locale, text) * 100000
                }
            }
            Label {
                text: "kI"
            }
            SpinBox {
                id: pid_ki
                editable: true
                from: 0
                to: 100000

                property int decimals: 5
                property real realValue: value / 100000

                textFromValue: function(value, locale) {
                    return Number(value / 100000).toLocaleString(locale, "f", pid_kp.decimals)
                }

                valueFromText: function(text, locale) {
                    return Number.fromLocaleString(locale, text) * 100000
                }
            }
            Label {
                text: "kD"
            }
            SpinBox {
                id: pid_kd
                editable: true
                from: 0
                to: 100000

                property int decimals: 5
                property real realValue: value / 100000

                textFromValue: function(value, locale) {
                    return Number(value / 100000).toLocaleString(locale, "f", pid_kp.decimals)
                }

                valueFromText: function(text, locale) {
                    return Number.fromLocaleString(locale, text) * 100000
                }
            }
            Button {
                text: "Send"
                onClicked: pidManager.forcePID(pid_kp.realValue, pid_ki.realValue, pid_kd.realValue)
            }
        }
    }

    Timer {
        id: locationUpdateTimer
        interval: 10
        repeat: true
        running: true
        triggeredOnStart: true
        onTriggered: locator.setLocation(0, 0)
    }

    Connections {
        target: locator
        onLocationUpdate: {
            appWin.heading = heading
            appWin.jetPos = QtPositioning.coordinate(lat, lng)
            marker.coordinate = appWin.jetPos
        }
    }
}
