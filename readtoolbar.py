# Copyright (C) 2006, Red Hat, Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

from gettext import gettext as _

import gobject
import gtk
import evince

try:
    import epubadapter
except:
    pass

from sugar.graphics.toolbutton import ToolButton
from sugar.graphics.menuitem import MenuItem
from sugar.graphics import iconentry
from sugar.activity import activity


class EditToolbar(activity.EditToolbar):

    __gtype_name__ = 'EditToolbar'

    def __init__(self):
        activity.EditToolbar.__init__(self)

        self._evince_view = None

        self._document = None
        self._find_job = None

        search_item = gtk.ToolItem()

        self._search_entry = iconentry.IconEntry()
        self._search_entry.set_icon_from_name(iconentry.ICON_ENTRY_PRIMARY,
                                                'system-search')
        self._search_entry.add_clear_button()
        self._search_entry.connect('activate', self._search_entry_activate_cb)
        self._search_entry.connect('changed', self._search_entry_changed_cb)
        self._search_entry_changed = True

        width = int(gtk.gdk.screen_width() / 3)
        self._search_entry.set_size_request(width, -1)

        search_item.add(self._search_entry)
        self._search_entry.show()

        self.insert(search_item, -1)
        search_item.show()

        self._prev = ToolButton('go-previous-paired')
        self._prev.set_tooltip(_('Previous'))
        self._prev.props.sensitive = False
        self._prev.connect('clicked', self._find_prev_cb)
        self.insert(self._prev, -1)
        self._prev.show()

        self._next = ToolButton('go-next-paired')
        self._next.set_tooltip(_('Next'))
        self._next.props.sensitive = False
        self._next.connect('clicked', self._find_next_cb)
        self.insert(self._next, -1)
        self._next.show()

    def set_view(self, view):
        self._evince_view = view
        self._evince_view.find_set_highlight_search(True)

    def set_document(self, document):
        self._document = document

    def _clear_find_job(self):
        if self._find_job is None:
            return
        if not self._find_job.is_finished():
            self._find_job.cancel()
        self._find_job.disconnect(self._find_updated_handler)
        self._find_job = None

    def _search_find_first(self):
        self._clear_find_job()
        text = self._search_entry.props.text
        if text != "":
            try:
                self._find_job = evince.JobFind(document=self._document, start_page=0, n_pages=self._document.get_n_pages(), text=text, case_sensitive=False)
                self._find_updated_handler = self._find_job.connect('updated', self._find_updated_cb)
                evince.job_scheduler_push_job(self._find_job, evince.JOB_PRIORITY_NONE)
            except TypeError:
                self._find_job = epubadapter.JobFind(document=self._document, start_page=0, n_pages=self._document.get_n_pages(), text=text, case_sensitive=False)
                self._find_updated_handler = self._find_job.connect('updated', self._find_updated_cb)
        else:
            # FIXME: highlight nothing
            pass

        self._search_entry_changed = False
        self._update_find_buttons()

    def _search_find_next(self):
        self._evince_view.find_next()

    def _search_find_last(self):
        # FIXME: does Evince support find last?
        return

    def _search_find_prev(self):
        self._evince_view.find_previous()

    def _search_entry_activate_cb(self, entry):
        if self._search_entry_changed:
            self._search_find_first()
        else:
            self._search_find_next()

    def _search_entry_changed_cb(self, entry):
        self._search_entry_changed = True
        self._update_find_buttons()

# Automatically start search, maybe after timeout?
#        self._search_find_first()

    def _find_changed_cb(self, page, spec):
        self._update_find_buttons()

    def _find_updated_cb(self, job, page=None):
        self._evince_view.find_changed(job, page)

    def _find_prev_cb(self, button):
        if self._search_entry_changed:
            self._search_find_last()
        else:
            self._search_find_prev()

    def _find_next_cb(self, button):
        if self._search_entry_changed:
            self._search_find_first()
        else:
            self._search_find_next()

    def _update_find_buttons(self):
        if self._search_entry_changed:
            if self._search_entry.props.text != "":
                self._prev.props.sensitive = False
#                self._prev.set_tooltip(_('Find last'))
                self._next.props.sensitive = True
                self._next.set_tooltip(_('Find first'))
            else:
                self._prev.props.sensitive = False
                self._next.props.sensitive = False
        else:
            self._prev.props.sensitive = True
            self._prev.set_tooltip(_('Find previous'))
            self._next.props.sensitive = True
            self._next.set_tooltip(_('Find next'))


class ViewToolbar(gtk.Toolbar):
    __gtype_name__ = 'ViewToolbar'

    __gsignals__ = {
        'needs-update-size': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE,
                              ([])),
        'go-fullscreen': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ([])),
    }

    def __init__(self):
        gtk.Toolbar.__init__(self)

        self._evince_view = None
        self._document = None

        self._zoom_out = ToolButton('zoom-out')
        self._zoom_out.set_tooltip(_('Zoom out'))
        self._zoom_out.connect('clicked', self._zoom_out_cb)
        self.insert(self._zoom_out, -1)
        self._zoom_out.show()

        self._zoom_in = ToolButton('zoom-in')
        self._zoom_in.set_tooltip(_('Zoom in'))
        self._zoom_in.connect('clicked', self._zoom_in_cb)
        self.insert(self._zoom_in, -1)
        self._zoom_in.show()

        self._zoom_to_width = ToolButton('zoom-best-fit')
        self._zoom_to_width.set_tooltip(_('Zoom to width'))
        self._zoom_to_width.connect('clicked', self._zoom_to_width_cb)
        self.insert(self._zoom_to_width, -1)
        self._zoom_to_width.show()

        palette = self._zoom_to_width.get_palette()
        menu_item = MenuItem(_('Zoom to fit'))
        menu_item.connect('activate', self._zoom_to_fit_menu_item_activate_cb)
        palette.menu.append(menu_item)
        menu_item.show()

        menu_item = MenuItem(_('Actual size'))
        menu_item.connect('activate', self._actual_size_menu_item_activate_cb)
        palette.menu.append(menu_item)
        menu_item.show()

        tool_item = gtk.ToolItem()
        self.insert(tool_item, -1)
        tool_item.show()

        self._zoom_spin = gtk.SpinButton()
        self._zoom_spin.set_range(5.409, 400)
        self._zoom_spin.set_increments(1, 10)
        self._zoom_spin_notify_value_handler = self._zoom_spin.connect(
                'notify::value', self._zoom_spin_notify_value_cb)
        tool_item.add(self._zoom_spin)
        self._zoom_spin.show()

        zoom_perc_label = gtk.Label(_("%"))
        zoom_perc_label.show()
        tool_item_zoom_perc_label = gtk.ToolItem()
        tool_item_zoom_perc_label.add(zoom_perc_label)
        self.insert(tool_item_zoom_perc_label, -1)
        tool_item_zoom_perc_label.show()

        spacer = gtk.SeparatorToolItem()
        spacer.props.draw = False
        self.insert(spacer, -1)
        spacer.show()

        self._fullscreen = ToolButton('view-fullscreen')
        self._fullscreen.set_tooltip(_('Fullscreen'))
        self._fullscreen.connect('clicked', self._fullscreen_cb)
        self.insert(self._fullscreen, -1)
        self._fullscreen.show()

        self._view_notify_zoom_handler = None

    def set_view(self, view):
        self._evince_view = view
        self._zoom_spin.props.value = self._evince_view.props.zoom * 100
        self._view_notify_zoom_handler = self._evince_view.connect(
            'notify::zoom', self._view_notify_zoom_cb)

        self._update_zoom_buttons()

    def _zoom_spin_notify_value_cb(self, zoom_spin, pspec):
        if not self._view_notify_zoom_handler:
            return
        self._evince_view.disconnect(self._view_notify_zoom_handler)
        try:
            if hasattr(self._evince_view.props, 'sizing_mode'):
                self._evince_view.props.sizing_mode = evince.SIZING_FREE
            self._evince_view.props.zoom = zoom_spin.props.value / 100.0
        finally:
            self._view_notify_zoom_handler = self._evince_view.connect(
                    'notify::zoom', self._view_notify_zoom_cb)

    def _view_notify_zoom_cb(self, evince_view, pspec):
        self._zoom_spin.disconnect(self._zoom_spin_notify_value_handler)
        try:
            self._zoom_spin.props.value = round(evince_view.props.zoom * 100.0)
        finally:
            self._zoom_spin_notify_value_handler = self._zoom_spin.connect(
                    'notify::value', self._zoom_spin_notify_value_cb)

    def zoom_in(self):
        if hasattr(self._evince_view.props, 'sizing_mode'):
            self._evince_view.props.sizing_mode = evince.SIZING_FREE
        self._evince_view.zoom_in()
        self._update_zoom_buttons()

    def _zoom_in_cb(self, button):
        self.zoom_in()

    def zoom_out(self):
        if hasattr(self._evince_view.props, 'sizing_mode'):
            self._evince_view.props.sizing_mode = evince.SIZING_FREE
        self._evince_view.zoom_out()
        self._update_zoom_buttons()

    def _zoom_out_cb(self, button):
        self.zoom_out()

    def zoom_to_width(self):
        if hasattr(self._evince_view.props, 'sizing_mode'):
            self._evince_view.props.sizing_mode = evince.SIZING_FIT_WIDTH
        self.emit('needs-update-size')
        self._update_zoom_buttons()

    def _zoom_to_width_cb(self, button):
        self.zoom_to_width()

    def _update_zoom_buttons(self):
        self._zoom_in.props.sensitive = self._evince_view.can_zoom_in()
        self._zoom_out.props.sensitive = self._evince_view.can_zoom_out()

    def _zoom_to_fit_menu_item_activate_cb(self, menu_item):
        if hasattr(self._evince_view.props, 'sizing_mode'): #XXX
            self._evince_view.props.sizing_mode = evince.SIZING_BEST_FIT
        self.emit('needs-update-size')
        self._update_zoom_buttons()

    def _actual_size_menu_item_activate_cb(self, menu_item):
        if hasattr(self._evince_view.props, 'sizing_mode'):
            self._evince_view.props.sizing_mode = evince.SIZING_FREE
        self._evince_view.props.zoom = 1.0
        self._update_zoom_buttons()

    def _fullscreen_cb(self, button):
        self.emit('go-fullscreen')
