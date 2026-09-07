import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import qs.Commons
import qs.Ui

Item {
  id: root
  property var shell: null
  property var barWidgetRegistry: null
  property var pluginRegistry: null
  property var manifest: null
  property string omarchyPath: ""
  property var status: ({visible: false, mode: "automatic", config: {widgets: [], monitor: ""}})
  property bool healthy: false
  property int failures: 0
  property int mountCount: 0
  property var tooltipTarget: null
  property string tooltipText: ""
  readonly property string position: "bottom"
  readonly property bool vertical: false
  readonly property int barSize: Style.bar.sizeHorizontal
  readonly property color foreground: Color.bar.text
  property color transparentForeground: Color.bar.text
  readonly property color contrastForeground: Color.background
  readonly property color barForeground: transparent ? transparentForeground : foreground
  readonly property color background: Color.bar.background
  readonly property color urgent: Color.bar.active
  readonly property string fontFamily: Style.font.family
  readonly property bool foregroundAnimationEnabled: true
  readonly property bool transparent: root.shell && root.shell.barConfig ? root.shell.barConfig.transparent === true : true
  property var entries: []
  readonly property var chosenScreen: {
    var screens = Quickshell.screens
    var name = status.config ? status.config.monitor : ""
    for (var i = 0; i < screens.length; i++) if (screens[i].name === name) return screens[i]
    return screens.length ? screens[0] : null
  }

  function refresh() { if (!poll.running) poll.running = true }
  function colorHex(value) {
    function channel(n) { return Math.round(Math.max(0, Math.min(1, n)) * 255).toString(16).padStart(2, "0") }
    return "#" + channel(value.r) + channel(value.g) + channel(value.b)
  }
  function refreshContrast() {
    if (!transparent || contrastProcess.running || !chosenScreen) return
    contrastProcess.command = ["omarchy-bar-text-color", "bottom", String(barSize + Style.space(12)),
      colorHex(foreground), colorHex(contrastForeground), "--screen",
      String(chosenScreen.width) + "x" + String(chosenScreen.height)]
    contrastProcess.running = true
  }
  function showTooltip(target, text) { tooltipTarget = target; tooltipText = text || "" }
  function hideTooltip(target) {
    if (!target || target === tooltipTarget) { tooltipTarget = null; tooltipText = "" }
  }
  function dismissWorkUi() {
    hideTooltip(null)
    var loader = shell && shell.panelLoaders ? shell.panelLoaders["omarchy.menu"] : null
    var menu = loader ? loader.item : null
    if (menu && menu.opened && String(menu.activeMenu).indexOf("trigger.work") === 0)
      shell.hide("omarchy.menu")
  }
  function moduleWidgets(name) {
    var result = []
    for (var i = 0; i < widgets.count; i++) {
      var loader = widgets.itemAt(i)
      if (loader && loader.item && loader.entry.id === name) result.push(loader.item)
    }
    return result
  }
  function inTopBar(id) {
    if (!shell || !shell.barConfig || !shell.barConfig.layout) return false
    var layout = shell.barConfig.layout
    for (var section of ["left", "center", "right"]) {
      var list = layout[section] || []
      for (var entry of list) if ((typeof entry === "string" ? entry : entry.id) === id) return true
    }
    return false
  }

  Component.onCompleted: refresh()
  onChosenScreenChanged: { hideTooltip(null); contrastTimer.restart() }
  onTransparentChanged: contrastTimer.restart()
  onForegroundChanged: contrastTimer.restart()
  onContrastForegroundChanged: contrastTimer.restart()
  Timer { id: contrastTimer; interval: 150; onTriggered: root.refreshContrast() }
  Process {
    id: contrastProcess
    stdout: SplitParser {
      onRead: function(line) {
        var value = String(line).trim()
        if (/^#[0-9a-fA-F]{6}$/.test(value)) root.transparentForeground = value
      }
    }
  }
  FileView {
    path: Quickshell.env("HOME") + "/.local/state/omarchy/current"
    watchChanges: true
    printErrors: false
    onFileChanged: contrastTimer.restart()
  }
  Timer { interval: 5000; repeat: true; running: true; onTriggered: root.refresh() }
  Process {
    id: poll
    command: [Quickshell.env("HOME") + "/.local/bin/two-bar", "status"]
    stdout: StdioCollector {
      onStreamFinished: {
        try {
          var next = JSON.parse(text)
          // Dismiss work UI on the transition, not on every hidden-state poll:
          // the user must be able to open Follow schedule while the bar is off.
          if (!next.visible && root.status.visible) root.dismissWorkUi()
          if (JSON.stringify(root.entries) !== JSON.stringify(next.config.widgets))
            root.entries = next.config.widgets
          if (JSON.stringify(root.status.config) === JSON.stringify(next.config))
            next.config = root.status.config
          root.status = next
          root.healthy = true
          root.failures = 0
        } catch (e) { root.healthy = false }
      }
    }
    onExited: function(code) {
      if (code !== 0) { root.failures++; root.healthy = false; root.hideTooltip(null) }
    }
  }
  IpcHandler {
    target: "two-bar"
    function refresh(): void { root.refresh() }
    function diagnostics(): string {
      var loaded = []
      var errors = []
      for (var i = 0; i < widgets.count; i++) {
        var loader = widgets.itemAt(i)
        if (loader && loader.item) loaded.push(loader.entry.id)
        if (loader && loader.status === Loader.Error) errors.push(loader.entry.id)
      }
      return JSON.stringify({visible: panel.visible, healthy: root.healthy, mode: root.status.mode,
        monitor: root.chosenScreen ? root.chosenScreen.name : "", loaded: loaded, errors: errors,
        tooltipVisible: tooltip.visible, transparent: root.transparent, foreground: root.colorHex(root.barForeground), mounts: root.mountCount})
    }
  }
  PanelWindow {
    id: panel
    screen: root.chosenScreen
    visible: root.healthy && root.status.visible && root.chosenScreen !== null && !remapGuard.remapping
    ScreenMoveRemap { id: remapGuard; window: panel }
    anchors { left: true; right: true; bottom: true }
    margins { bottom: Style.space(8) }
    implicitWidth: 0
    implicitHeight: root.barSize + Style.space(4)
    exclusionMode: ExclusionMode.Auto
    mask: Region { item: card }
    color: "transparent"
    WlrLayershell.namespace: "two-bar"
    WlrLayershell.layer: WlrLayer.Top
    onVisibleChanged: if (!visible) root.dismissWorkUi()

    Rectangle {
      id: card
      anchors.left: parent.left
      anchors.leftMargin: Style.space(8)
      width: row.implicitWidth + Style.space(12)
      height: parent.height
      color: root.transparent ? "transparent" : root.background
      radius: Style.cornerRadius
      border.color: Color.bar.text
      border.width: root.transparent ? 0 : 1
    }
    Row {
      id: row
      anchors.centerIn: card
      spacing: Style.space(4)
      WidgetButton {
        bar: root
        text: "󰃖"
        tooltipText: "Work bar · " + root.status.mode + "\nClick for work controls"
        onPressed: if (root.shell) root.shell.summon("omarchy.menu", JSON.stringify({menu: "trigger.work"}))
      }
      Repeater {
        id: widgets
        model: root.entries
        Loader {
          id: widgetLoader
          required property var modelData
          readonly property var entry: modelData
          readonly property var registered: root.barWidgetRegistry ? root.barWidgetRegistry.widgets[entry.id] : null
          active: panel.visible && !root.inTopBar(entry.id)
          sourceComponent: registered ? registered.component : null
          width: item ? item.implicitWidth : 0
          height: item ? item.implicitHeight : 0
          onLoaded: {
            root.mountCount++
            item.bar = root
            item.moduleName = entry.id
            item.settings = entry
          }
          onActiveChanged: if (!active) root.hideTooltip(null)
        }
      }
      Text {
        visible: root.entries.some(function(entry) {
          return root.inTopBar(entry.id) || !root.barWidgetRegistry || !root.barWidgetRegistry.widgets[entry.id]
        })
        text: "Widget unavailable"
        color: root.foreground
        font.family: root.fontFamily
        font.pixelSize: Style.font.caption
        height: root.barSize
        verticalAlignment: Text.AlignVCenter
      }
    }
    PopupWindow {
      id: tooltip
      visible: panel.visible && root.tooltipTarget !== null && root.tooltipText !== ""
      color: "transparent"
      implicitWidth: bubble.width
      implicitHeight: bubble.height
      anchor {
        id: tooltipAnchor
        window: panel
        adjustment: PopupAdjustment.Slide
        edges: Edges.Top | Edges.Left
        gravity: Edges.Bottom | Edges.Right
        rect.width: 1
        rect.height: 1
        onAnchoring: {
          if (!root.tooltipTarget) return
          var point = panel.contentItem.mapFromItem(root.tooltipTarget, 0, -tooltip.height - 6)
          tooltipAnchor.rect.x = Math.round(point.x)
          tooltipAnchor.rect.y = Math.round(point.y)
        }
      }
      Rectangle {
        id: bubble
        width: Math.min(label.implicitWidth + 20, 480)
        height: label.implicitHeight + 14
        color: Color.tooltip.background
        radius: Style.cornerRadius
        border.color: Color.tooltip.border
        Text {
          id: label
          anchors.centerIn: parent
          width: Math.min(implicitWidth, 460)
          text: root.tooltipText
          textFormat: Text.PlainText
          wrapMode: Text.Wrap
          color: Color.tooltip.text
          font.family: root.fontFamily
          font.pixelSize: Style.font.body
        }
      }
    }
  }
}
