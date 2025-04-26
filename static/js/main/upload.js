var inp = document.getElementById('pic');

document.getElementById("pic-input").addEventListener("change", function () {
    const file = this.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = function (event) {
        const imageData = event.target.result;
        sendImage(imageData);
    };
    reader.readAsDataURL(file);
});
function sendImage(imageData){
    document.getElementById('pic').value = imageData; 
}