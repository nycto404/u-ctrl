const toggleThemeButton = document.getElementById('toggle-theme-button');
const toggleThemeButtonIcon = document.getElementById('toggle-theme-button-icon');
const savedTheme = localStorage.getItem('u-webui-theme');


let setInitialTheme = () => {
    let theme = localStorage.getItem("u-webui-theme");
    document.documentElement.setAttribute('data-theme', theme);
    if (theme == "light") {
        toggleThemeButton.className = "btn btn-dark";
        toggleThemeButtonIcon.className = "fa-solid fa-moon";
    } else {
        toggleThemeButton.className = "btn btn-light";
        toggleThemeButtonIcon.className = "fa-solid fa-sun";
    }
}

let toggleTheme = () => {
    let currentTheme = localStorage.getItem("u-webui-theme");

    if (currentTheme == 'light') {
        document.documentElement.setAttribute('data-theme', 'dark');
        localStorage.setItem('u-webui-theme', 'dark');
        toggleThemeButton.className = "btn btn-light";
        toggleThemeButtonIcon.className = "fa-solid fa-sun";
    } else {
        document.documentElement.setAttribute('data-theme', 'light');
        localStorage.setItem('u-webui-theme', 'light');
        toggleThemeButton.className = "btn btn-dark";    
        toggleThemeButtonIcon.className = "fa-solid fa-moon";
    }
}



setInitialTheme();


toggleThemeButton.addEventListener("click", toggleTheme);