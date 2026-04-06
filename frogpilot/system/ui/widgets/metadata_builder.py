from openpilot.common.params import ParamKeyType
from openpilot.system.ui.lib.multilang import tr

from openpilot.frogpilot.system.ui.widgets.buttons_action import buttons_item
from openpilot.frogpilot.system.ui.widgets.dual_param_value import dual_param_value_item
from openpilot.frogpilot.system.ui.widgets.list_view import button_item, text_item, toggle_item
from openpilot.frogpilot.system.ui.widgets.manage_toggle import manage_toggle_item
from openpilot.frogpilot.system.ui.widgets.multiple_button import multiple_button_item
from openpilot.frogpilot.system.ui.widgets.multiple_button_toggle import multiple_button_toggle_item
from openpilot.frogpilot.system.ui.widgets.param_value import FrogPilotParamValueAction, param_value_item
from openpilot.frogpilot.system.ui.widgets.param_value_button import param_value_button_item
from openpilot.frogpilot.system.ui.widgets.param_value_toggle import param_value_toggle_item
from openpilot.frogpilot.system.ui.widgets.unit_conversion import display_to_si, get_maximum, get_minimum, get_unit, get_value_map, is_metric, si_to_display
from openpilot.frogpilot.ui.layouts.settings.toggle_metadata import WidgetType


class MetadataWidgetBuilderMixin:
  @staticmethod
  def _step_precision(step):
    if not isinstance(step, (int, float)) or float(step).is_integer():
      return None
    step_text = f"{step:.10f}".rstrip("0")
    return len(step_text.split(".")[1]) if "." in step_text else None

  def _build_metadata_item(self, item_key, spec, *, subviews=None):
    subviews = subviews or {}

    builders = {
      WidgetType.BUTTON:                  lambda: self._build_button(item_key, spec, subviews),
      WidgetType.BUTTONS:                 lambda: self._build_buttons(spec, subviews),
      WidgetType.MULTIPLE_BUTTON:         lambda: self._build_multiple_button(item_key, spec),
      WidgetType.TEXT:                     lambda: self._build_text(item_key, spec),
      WidgetType.TUNING_DUAL_PARAM_VALUE: lambda: self._build_dual_param_value(spec),
      WidgetType.TUNING_MANAGE_TOGGLE:    lambda: self._build_manage_toggle(item_key, spec, subviews),
      WidgetType.TUNING_PARAM_VALUE:      lambda: self._build_param_value(spec),
      WidgetType.TUNING_PARAM_VALUE_BUTTON: lambda: self._build_param_value_button(spec),
      WidgetType.TUNING_TOGGLE:           lambda: self._build_toggle(spec),
    }

    builder = builders.get(spec.widget_type)
    if builder is None:
      raise ValueError(f"Unsupported widget type: {spec.widget_type}")
    return builder()

  # ── Widget builders ────────────────────────────────────────────────

  def _build_button(self, item_key, spec, subviews):
    on_method = getattr(self, f"_on_{item_key}", None)
    value_method = getattr(self, f"_value_{item_key}", None)
    text_method = getattr(self, f"_text_{item_key}", None)
    visible = self._visibility(spec)

    return self._with_tuning(spec.param_key, button_item(
      self._tr(spec.title),
      text_method or self._tr(spec.button_text),
      description=self._tr(spec.description),
      callback=on_method or (lambda ik=item_key: self._set_view(subviews[ik])),
      icon=spec.icon,
      value=value_method,
    ), visible=visible)

  def _build_buttons(self, spec, subviews):
    def resolve_callback(action):
      method = getattr(self, f"_on_{action}", None)
      return method or (lambda a=action: self._set_view(subviews[a]))

    buttons = []
    for b in spec.buttons:
      button_dict = {"text": self._tr(b.text), "callback": resolve_callback(b.action)}
      button_visible = self._button_visible(b.action)
      if button_visible is not True:
        button_dict["visible"] = button_visible
      buttons.append(button_dict)

    visible = self._visibility(spec)

    return self._with_tuning(None, buttons_item(
      self._tr(spec.title),
      description=self._tr(spec.description),
      buttons=buttons,
      icon=spec.icon,
    ), visible=visible)

  def _button_visible(self, action: str):
    """Override in subclasses to control per-button visibility. Return True (default), False, or a callable."""
    return True

  def _build_dual_param_value(self, spec):
    left = self._make_param_action(spec)
    right = self._make_param_action(spec.secondary)

    return self._with_tuning(spec.param_key, dual_param_value_item(
      self._title(spec),
      description=self._tr(spec.description),
      left=left,
      right=right,
      right_title=self._tr(spec.secondary.title),
      right_description=self._tr(spec.secondary.description),
    ))

  def _build_manage_toggle(self, item_key, spec, subviews):
    pk = spec.param_key

    return self._with_tuning(pk, manage_toggle_item(
      self._tr(spec.title),
      self._tr(spec.button_text),
      description=self._tr(spec.description),
      initial_state=self.params.get_bool(pk),
      state_getter=lambda pk=pk: self.params.get_bool(pk),
      toggle_callback=self._bool_param_callback(pk, reboot=spec.reboot, refreshes_visibility=spec.refreshes_visibility),
      callback=lambda ik=item_key: self._set_view(subviews[ik]),
      icon=spec.icon,
    ))

  def _build_multiple_button(self, item_key, spec):
    item = multiple_button_item(
      self._tr(spec.title),
      description=self._tr(spec.description),
      buttons=self._option_sources(spec),
      selected_index=self._multi_button_index(item_key, spec),
      callback=self._multi_button_callback(item_key, spec),
      icon=spec.icon,
    )
    self._multiple_button_items[item_key] = item
    return item

  def _build_param_value(self, spec):
    pk = spec.param_key
    mn, mx = self._min_max(spec)
    si = self._si_converters(spec)
    visible = self._visibility(spec)
    child_keys = self._child_bool_keys(spec.child_param_keys, len(spec.options))

    if child_keys:
      states_getter, toggle_callback = self._child_bool_controls(child_keys)
      return self._with_tuning(pk, param_value_toggle_item(
        self._title(spec),
        description=self._tr(spec.description),
        param_key=pk,
        minimum=mn,
        maximum=mx,
        width_values=self._width_values(spec),
        step=spec.step,
        buttons=self._option_sources(spec),
        button_states_getter=states_getter,
        button_toggle_callback=toggle_callback,
        value_formatter=self._value_formatter(spec),
        **si,
      ), visible=visible)

    return self._with_tuning(pk, param_value_item(
      self._title(spec),
      description=self._tr(spec.description),
      param_key=pk,
      minimum=mn,
      maximum=mx,
      width_values=self._width_values(spec),
      step=spec.step,
      value_formatter=self._value_formatter(spec),
      **si,
    ), visible=visible)

  def _build_param_value_button(self, spec):
    pk = spec.param_key
    mn, mx = self._min_max(spec)
    callback_method = getattr(self, spec.button_callback_method)

    return self._with_tuning(pk, param_value_button_item(
      self._title(spec),
      description=self._tr(spec.description),
      param_key=pk,
      minimum=mn,
      maximum=mx,
      width_values=self._width_values(spec),
      step=spec.step,
      button_text=self._tr(spec.button_text),
      button_callback=lambda pk=pk: callback_method(pk),
      value_formatter=self._value_formatter(spec),
      **self._si_converters(spec),
    ))

  def _build_text(self, item_key, spec):
    pk = spec.param_key
    vmap = spec.value_map or {}
    unit = spec.unit or ""
    precision = spec.display_precision
    static = spec.value_text
    override = getattr(self, f"_value_{item_key}", None)

    if override is not None:
      value_source = override
    elif static is not None:
      value_source = lambda: tr(static)
    elif pk is None:
      value_source = lambda: ""
    else:
      cached = [self._format_value(self.params.get(pk), vmap, unit, precision)]
      self._visibility_updaters.append(lambda: cached.__setitem__(0, self._format_value(self.params.get(pk), vmap, unit, precision)))
      value_source = lambda c=cached: c[0]

    return self._with_tuning(pk, text_item(
      self._tr(spec.title),
      value=value_source,
      description=self._tr(spec.description),
    ))

  def _build_toggle(self, spec):
    pk = spec.param_key
    visible = self._visibility(spec, use_child_visibility=not spec.options)
    child_keys = self._child_bool_keys(spec.child_param_keys, len(spec.options))

    if child_keys:
      states_getter, toggle_callback = self._child_bool_controls(child_keys)
      return self._with_tuning(pk, multiple_button_toggle_item(
        self._tr(spec.title),
        description=self._tr(spec.description),
        buttons=self._option_sources(spec),
        toggle_initial_state=self.params.get_bool(pk),
        toggle_callback=self._bool_param_callback(pk, reboot=spec.reboot, refreshes_visibility=spec.refreshes_visibility),
        button_states_getter=states_getter,
        button_toggle_callback=toggle_callback,
        state_getter=lambda pk=pk: self.params.get_bool(pk),
        icon=spec.icon,
      ), visible=visible)

    return self._with_tuning(pk, toggle_item(
      self._tr(spec.title),
      description=self._tr(spec.description),
      initial_state=self.params.get_bool(pk),
      callback=self._bool_param_callback(pk, reboot=spec.reboot, refreshes_visibility=spec.refreshes_visibility),
      icon=spec.icon,
    ), visible=visible)

  # ── Child param helpers ────────────────────────────────────────────

  def _child_bool_keys(self, child_param_keys, option_count=None):
    if not child_param_keys:
      return ()
    if option_count is not None and len(child_param_keys) != option_count:
      return ()
    if not all(self.params.get_type(k) == ParamKeyType.BOOL for k in child_param_keys):
      return ()
    return child_param_keys

  def _child_bool_controls(self, child_keys):
    cache = [self.params.get_bool(k) for k in child_keys]
    self._visibility_updaters.append(lambda ck=child_keys, c=cache: [c.__setitem__(i, self.params.get_bool(k)) for i, k in enumerate(ck)])

    def getter(c=cache):
      return c

    def toggler(i, ck=child_keys, c=cache):
      c[i] = not c[i]
      self.params.put_bool(ck[i], c[i])

    return getter, toggler

  # ── Multiple button helpers ────────────────────────────────────────

  def _multi_button_index(self, item_key, spec):
    child_keys = self._child_bool_keys(spec.child_param_keys)
    if child_keys:
      for i, key in enumerate(child_keys):
        if self.params.get_bool(key):
          return i
      return len(spec.options) - 1 if len(spec.options) > len(child_keys) else 0

    if spec.param_key is not None:
      return min(self.params.get(spec.param_key) or 0, len(spec.options) - 1)

    raise ValueError(f"Unsupported multiple-button item: {item_key}")

  def _multi_button_callback(self, item_key, spec):
    child_keys = self._child_bool_keys(spec.child_param_keys)
    if child_keys:
      def callback(index):
        for key in child_keys:
          self.params.put_bool(key, False)
        if 0 <= index < len(child_keys):
          self.params.put_bool(child_keys[index], True)
      return callback

    if spec.param_key is not None:
      pk = spec.param_key
      return lambda index, pk=pk: self.params.put(pk, index)

    raise ValueError(f"Unsupported multiple-button item: {item_key}")

  # ── Value formatting ───────────────────────────────────────────────

  @staticmethod
  def _format_value(value, value_map, unit, precision=None):
    if value in value_map:
      return value_map[value]
    if value is None:
      return ""

    if isinstance(value, (int, float)):
      if precision is not None:
        text = f"{float(value):.{precision}f}"
      elif float(value).is_integer():
        text = f"{int(value)}"
      else:
        text = f"{value:g}"
    else:
      text = str(value)

    return f"{text}{unit}" if unit else text

  def _value_formatter(self, spec):
    precision = spec.display_precision if spec.display_precision is not None else self._step_precision(spec.step)

    if spec.unit_type is not None:
      ut = spec.unit_type
      base_map = spec.value_map or {}
      def formatter(value, bm=base_map, ut=ut, p=precision):
        return self._format_value(value, get_value_map(ut, bm) or {}, get_unit(ut), p)
      return formatter

    vmap = spec.value_map or {}
    unit = spec.unit or ""
    return lambda value, vm=vmap, u=unit, p=precision: self._format_value(value, vm, u, p)

  # ── Metric / unit helpers ──────────────────────────────────────────

  def _min_max(self, spec):
    if spec.unit_type is not None:
      ut, base_min = spec.unit_type, spec.minimum
      return lambda: get_minimum(ut, base_min), lambda: get_maximum(ut)
    if spec.minimum is not None and spec.maximum is not None:
      return spec.minimum, spec.maximum
    if spec.minimum_callback_method is not None and spec.maximum_callback_method is not None:
      return getattr(self, spec.minimum_callback_method), getattr(self, spec.maximum_callback_method)

    raise ValueError(f"Missing numeric bounds for {spec.param_key or spec.title}")

  @staticmethod
  def _si_converters(spec):
    if spec.unit_type is None:
      return {}
    ut = spec.unit_type
    return {
      "si_to_display": lambda value, ut=ut: si_to_display(ut, value),
      "display_to_si": lambda value, ut=ut: display_to_si(ut, value),
    }

  @staticmethod
  def _width_values(spec):
    if spec.unit_type is not None:
      return tuple((get_value_map(spec.unit_type, spec.value_map) or {}).keys())
    return tuple((spec.value_map or {}).keys())

  def _title(self, spec):
    if spec.title_callback_method is not None:
      return getattr(self, spec.title_callback_method)
    if spec.metric_title is not None:
      imperial, metric = spec.title, spec.metric_title
      return lambda: tr(metric if is_metric() else imperial)
    return self._tr(spec.title)

  # ── Translation / options ──────────────────────────────────────────

  def _option_sources(self, spec):
    return [self._tr(label) for label in spec.options]

  @staticmethod
  def _tr(text):
    return lambda text=text if text is not None else "": tr(text)

  # ── Visibility ─────────────────────────────────────────────────────

  def _visibility(self, spec, *, use_child_visibility=False):
    if spec.visible_state is not None:
      states = (spec.visible_state,) if isinstance(spec.visible_state, str) else spec.visible_state
      return lambda states=states: all(self.VISIBILITY_STATES[s](self) for s in states)

    if use_child_visibility:
      child_keys = self._child_bool_keys(spec.child_param_keys)
      if child_keys:
        return lambda ck=child_keys: any(self.params.get_bool(k) for k in ck)

    return True

  def _with_tuning(self, key, item, visible=True):
    self._set_tuning_level_visible(item, key, visible)
    return item

  # ── Param value action (for dual controls) ─────────────────────────

  def _make_param_action(self, spec):
    mn, mx = self._min_max(spec)
    return FrogPilotParamValueAction(
      param_key=spec.param_key,
      minimum=mn,
      maximum=mx,
      width_values=self._width_values(spec),
      value_formatter=self._value_formatter(spec),
      step=spec.step,
      **self._si_converters(spec),
    )
