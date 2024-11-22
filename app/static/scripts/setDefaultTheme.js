// If theme is not found in localstorage, then save it
if (!localStorage.getItem("u-webui-theme")) {
    localStorage.setItem("u-webui-theme", "light");
};