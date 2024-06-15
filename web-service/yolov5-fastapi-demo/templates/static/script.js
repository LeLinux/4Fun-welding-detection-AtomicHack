const camera_button = document.getElementById("camera");
const folder_button = document.getElementById("folder");
const test_img = document.getElementById('test');
const file_dialog = document.getElementById("file_dialog");
const camera_input = document.getElementById("cameraInput");




folder_button.addEventListener("click",
  (e) => {
    if (file_dialog) {
      file_dialog.click();
    }
    e.preventDefault(); // prevent navigation to "#"
  },
  false,)


file_dialog.addEventListener("change", handleFiles, false);  
function handleFiles(){

    test_img.src = URL.createObjectURL(this.files[0]);

}
    

camera_button.addEventListener("click",
    (e) => {
        if(camera_input){
            camera_input.click();
        }
        e.preventDefault();
    },
    false,
);

camera_input.addEventListener("change", handlePhoto, false);  
function handlePhoto(){

    test_img.src = URL.createObjectURL(this.files[0]);

}