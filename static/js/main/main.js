
document.addEventListener('DOMContentLoaded', ()=>{
  console.log('Initialised JS')
  const links = document.querySelectorAll('.pc-ul li')
  links.forEach(link =>{
    var dest = link.getAttribute('data-href')
    const tc = link.querySelector('.tc')
    link.title = tc.innerText
    link.addEventListener('click', ()=>{
      if(dest){
        window.location.href = dest
      }
     })
  }) 
  const inputs = document.querySelectorAll('input')
  inputs.forEach(input =>{
    let name = input.getAttribute('name')
    let labels = document.querySelectorAll('#addStudentForm legend label')
    labels.forEach(label => {
      let l_for = label.getAttribute('for')
      if(l_for==name){
        input.placeholder = label.innerHTML
      }
    })
  })

  const mb = document.querySelector('.menu-toggle');
  const sidebar = document.querySelector('.sidebar')
  mb.addEventListener('click', ()=>{
    mb.classList.toggle('active')
    sidebar.classList.toggle('appear')
    toggleText()

  })

  function toggleText(){
    links.forEach(link=>{
      const tc = link.querySelector('.tc')
      tc.classList.toggle('none')
    })
  }
  const cb = document.querySelector('.closeBtn')
const notifDiv = document.querySelector('.notifDiv')
const notifInner = document.querySelector('.notifDiv-inner')
  notifDiv.addEventListener('click', (e)=>{
    if(e.target != notifInner && e.target != cb && !notifInner.contains(e.target)){
      notifAction()
    }
  })

  const notifSeen = document.getElementById('notifInner');
  let notifs = document.querySelectorAll('.notification');
  
  notifs.forEach(notif => {
    const words = notif.innerHTML.split(/\s+/).slice(0, 20).join(' ');
  
    const notifClasses = Array.from(notif.classList).filter(c => c !== 'notification');
    notifSeen.classList.add(...notifClasses);
    notifSeen.classList.add('bdr-10');
    notifSeen.classList.add('pd-10');
  
    notifSeen.innerHTML = `
      <div>
        ${words}...<br>
        <a href="javascript:void(0)" class="c-p f-s-s cl-bl" style="font-style:italic;" onclick="notifAction()">See More</a>
      </div>
    `;
  });
  
  
})





function notifAction(){
  const cb = document.querySelector('.closeBtn')
  const notifDiv = document.querySelector('.notifDiv')
if(cb){
if(notifDiv){
  notifDiv.classList.toggle('flex')
  notifDiv.classList.toggle('none')
}
}
}


