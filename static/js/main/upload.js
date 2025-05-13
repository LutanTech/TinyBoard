document.addEventListener('DOMContentLoaded', () => {
    function handleImageInput(inputSelector, targetSelector) {
        const input = document.querySelector(inputSelector);
        if (input) {
            console.log(`${inputSelector} found`);
            input.addEventListener("change", function () {
                console.log(`listening for change on ${inputSelector}`);
                const file = this.files[0];
                if (!file) return;

                const reader = new FileReader();
                reader.onload = function (event) {
                    document.querySelector(targetSelector).value = event.target.result;
                };
                reader.readAsDataURL(file);
            });
        }
    }

    handleImageInput('#pic-input', '#pic');
    handleImageInput('#pic-input1', '#pic1');
    handleImageInput('#pic-input2', 'form #pic2');
});
