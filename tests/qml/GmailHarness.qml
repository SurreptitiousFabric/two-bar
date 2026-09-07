import QtQuick
import Quickshell
import Quickshell.Io

ShellRoot {
  Component { id: gmailComponent; Gmail {} }
  WorkPanel {
    id: host
    shell: QtObject { property var barConfig: ({transparent: true, layout: {}}) }
    barWidgetRegistry: QtObject {
      property var widgets: ({"local.gmail-monitor": {component: gmailComponent}})
    }
  }
  function widget() { return host.moduleWidgets("local.gmail-monitor")[0] }
  function button() {
    var item = widget()
    if (!item) return null
    for (var child of item.children) if (typeof child.triggerPress === "function") return child
    return null
  }
  IpcHandler {
    target: "validation"
    function snapshot(): string {
      var w = widget(), b = button()
      return JSON.stringify(w && b ? {ready: true, healthy: w.statusHealthy,
        unread: w.unreadCount, active: b.active, dimmed: b.dimmed, tooltip: b.tooltipText} : {ready: false})
    }
    function apply(data: string): void { widget().applyStatus(data) }
    function hover(): void { var b = button(); host.showTooltip(b, b.tooltipText) }
    function click(right: bool): void { button().triggerPress(right ? Qt.RightButton : Qt.LeftButton) }
  }
}
