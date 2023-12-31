javascript:(function(){var style = document.createElement('style'); style.innerHTML = 'img[alt="User"] {visibility:hidden;}';document.head.appendChild(style);var style2=document.createElement('style');style2.innerHTML='main div.relative:has(> svg[fill="none"][role="img"])::before,main div.relative:has(> svg[fill="none"][stroke-linecap="round"][stroke-linejoin="round"])::before {content: url("https://pbs.twimg.com/profile_images/1496241686477144064/U3T0oV6o_x96.jpg");display: inline-block;transform: scale(.667) translate(-20%, 10%);}@media(max-width:400px){main div.relative:has(> svg[fill="none"][role="img"])::before,main div.relative:has(> svg[fill="none"][stroke-linecap="round"][stroke-linejoin="round"])::before {content: url("https://pbs.twimg.com/profile_images/1496241686477144064/U3T0oV6o_x96.jpg");display: inline-block;transform: scale(.500) translate(0%, 10%);}}main div > svg[fill="none"][role="img"] {padding:0 !important;}';document.head.appendChild(style2);})();

function() {
    var style = document.createElement('style');
    style.innerHTML = `
        img[alt="User"] {
            visibility: hidden;
        }`;
    document.head.appendChild(style);
    
    var style2 = document.createElement('style');
    style2.innerHTML = `
        main div.relative:has(> svg[fill="none"][role="img"])::before,
        main div.relative:has(> svg[fill="none"][stroke-linecap="round"][stroke-linejoin="round"])::before {
            content: url("https://pbs.twimg.com/profile_images/1496241686477144064/U3T0oV6o_x96.jpg");
            display: inline-block;
            transform: scale(.400) translate(-20%, 20%);
        }
        main div > svg[fill="none"][role="img"] {
            padding: 0 !important;
        }`;
    document.head.appendChild(style2);
}