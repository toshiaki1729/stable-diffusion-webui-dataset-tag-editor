from collections import namedtuple
import json

from scripts import logger
from scripts.paths import paths
from scripts.dte_instance import dte_instance

SortBy = dte_instance.SortBy
SortOrder = dte_instance.SortOrder

CONFIG_PATH = paths.base_path / "config.json"

GeneralConfig = namedtuple(
    "GeneralConfig",
    [
        "backup",
        "dataset_dir",
        "caption_ext",
        "load_recursive",
        "load_caption_from_filename",
        "replace_new_line",
        "use_interrogator",
        "use_interrogator_names",
        "use_custom_threshold_booru",
        "custom_threshold_booru",
        "use_custom_threshold_waifu",
        "custom_threshold_waifu",
        "custom_threshold_z3d",
        "save_kohya_metadata",
        "meta_output_path",
        "meta_input_path",
        "meta_overwrite",
        "meta_save_as_caption",
        "meta_use_full_path",
    ],
)
FilterConfig = namedtuple(
    "FilterConfig",
    ["sw_prefix", "sw_suffix", "sw_regex", "sort_by", "sort_order", "logic"],
)
BatchEditConfig = namedtuple(
    "BatchEditConfig",
    [
        "show_only_selected",
        "prepend",
        "use_regex",
        "target",
        "sw_prefix",
        "sw_suffix",
        "sw_regex",
        "sory_by",
        "sort_order",
        "batch_sort_by",
        "batch_sort_order",
        "token_count",
    ],
)
EditSelectedConfig = namedtuple(
    "EditSelectedConfig",
    [
        "auto_copy",
        "sort_on_save",
        "warn_change_not_saved",
        "use_interrogator_name",
        "sort_by",
        "sort_order",
    ],
)
MoveDeleteConfig = namedtuple(
    "MoveDeleteConfig", ["range", "target", "caption_ext", "destination"]
)

CFG_GENERAL_DEFAULT = GeneralConfig(
    True,
    "",
    ".txt",
    False,
    True,
    False,
    "No",
    [],
    False,
    0.7,
    False,
    0.35,
    0.35,
    False,
    "",
    "",
    True,
    False,
    False,
)
CFG_FILTER_P_DEFAULT = FilterConfig(
    False, False, False, SortBy.ALPHA.value, SortOrder.ASC.value, "AND"
)
CFG_FILTER_N_DEFAULT = FilterConfig(
    False, False, False, SortBy.ALPHA.value, SortOrder.ASC.value, "OR"
)
CFG_BATCH_EDIT_DEFAULT = BatchEditConfig(
    True,
    False,
    False,
    "Only Selected Tags",
    False,
    False,
    False,
    SortBy.ALPHA.value,
    SortOrder.ASC.value,
    SortBy.ALPHA.value,
    SortOrder.ASC.value,
    75,
)
CFG_EDIT_SELECTED_DEFAULT = EditSelectedConfig(
    False, False, False, "", SortBy.ALPHA.value, SortOrder.ASC.value
)
CFG_MOVE_DELETE_DEFAULT = MoveDeleteConfig("Selected One", [], ".txt", "")


class Config:
    def __init__(self):
        self.config = dict()

    def load(self):
        if not CONFIG_PATH.is_file():
            self.config = dict()
            return
        try:
            self.config = json.loads(CONFIG_PATH.read_text("utf8"))
        except:
            logger.warn("Error on loading config.json. Default settings will be loaded.")
            self.config = dict()
        else:
            logger.write("Settings has been read from config.json")

    def save(self):
        CONFIG_PATH.write_text(json.dumps(self.config, indent=4), "utf8")

    def read(self, name: str):
        return self.config.get(name)

    def write(self, cfg: dict, name: str):
        self.config[name] = cfg
