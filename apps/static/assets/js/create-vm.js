
  let currentStep = 0;
  const steps = document.querySelectorAll('.step');
  const stepIndicators = document.querySelectorAll('.step-indicator');
  const progressBar = document.querySelector('.progress-bar');

  function showStep(step) {
    steps.forEach((el, index) => {
      el.classList.toggle('active', index === step);
      stepIndicators[index].classList.toggle('active', index <= step);
    });
    progressBar.style.width = ((step / (steps.length - 1)) * 100) + '%';
  }

  function nextStep() {
    if (currentStep < steps.length - 1) {
      currentStep++;
      showStep(currentStep);
    }
  }

  function prevStep() {
    if (currentStep > 0) {
      currentStep--;
      showStep(currentStep);
    }
  }

  // Initialize first step as active
  document.addEventListener('DOMContentLoaded', (event) => {
    showStep(currentStep);
  });
  //validate input
  document.addEventListener("DOMContentLoaded", function() {
    const vm_idInput = document.getElementById('vm_id');
    const vmNameInput = document.getElementById('vm_name');
    const vmMemoryInput = document.getElementById('vm_memory');
    const vmCoresInput = document.getElementById('vm_cores');
    const vmDiskInput = document.getElementById('vm_disk');
    const vmBridgeInput = document.getElementById('vm_bridge');
    const isoImageInput = document.getElementById('iso_image');
    const osTypeInput = document.getElementById('ostype');
    const nodeSelect = document.getElementById('nodeSelect');

    const submitBtn = document.getElementById('submitBtn');
    const errorMessage = document.getElementById('error-message');
    let isTouched =false
    vm_idInput.addEventListener('focus', function() {
        isTouched = true;
    });

   const inputs = [
        vm_idInput, vmNameInput, vmMemoryInput, vmCoresInput,
        vmDiskInput, vmBridgeInput, isoImageInput, osTypeInput,nodeSelect
    ];
    inputs.forEach(input => {
        input.addEventListener('input', validateInput);
        input.addEventListener('blur', validateInput);
    });



    const spinner = document.getElementById('spinner');
    const form = document.getElementById('multiStepForm');
   // Handle form submission

    form.addEventListener('submit', function (event) {
        event.preventDefault();
        spinner.style.visibility = 'visible';

        const formData = new FormData(form);

        fetch(form.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        })
            .then(response => response.json()
            )
            .then(data => {
                spinner.style.visibility = 'hidden';

                if (data.success) {
                     window.location.href=`/vm-info/${vmid}/`
                    alert('Form submitted successfully!');
                    //window.redi
                    // Optionally redirect or handle success
                } else {
                    alert('Form submitted successfully : ' );
                     window.location.href=`/vm-info/${vmid}/`
                    // Optionally handle form submission errors
                }
            })
            .catch(error => {
                spinner.style.visibility = 'hidden';
                 window.location.href='/list-vms/'
               // console.error('Form submission error:', error);
                alert('Form submitted succesfully : ');
            });
    });






});

    function validateInput(event) {
        const input = event.target;
        const errorMessage = input.nextElementSibling;

        if (!input.validity.valid || input.value.trim() === '') {
            input.classList.add('invalid');
            if (errorMessage && errorMessage.classList.contains('error-message')) {
                errorMessage.style.visibility = 'visible';
                errorMessage.textContent = `Invalid ${input.name.replace('_', ' ')}`;
                            submitBtn.disabled = true;

            }
        } else {
            input.classList.remove('invalid');
            if (errorMessage && errorMessage.classList.contains('error-message')) {
                errorMessage.style.visibility = 'hidden';
                            submitBtn.disabled = false;

            }
        }}

  //end validate

  document.addEventListener('DOMContentLoaded', function () {
    fetch('/proxmox/nodes/')
      .then(response => response.json())
      .then(data => {
        if (data.error) {
          console.error('Error fetching nodes:', data.error);
          const nodeSelect = document.getElementById('nodeSelect');
          nodeSelect.innerHTML = '<option selected disabled>Error loading nodes</option>';
          return;
        }

        const nodeSelect = document.getElementById('nodeSelect');
        nodeSelect.innerHTML = '<option selected disabled>Select a node</option>';
        data.nodes.forEach(node => {
          const option = document.createElement('option');
          option.value = node.name;
          option.textContent = `${node.name} (${node.status})`;
          nodeSelect.appendChild(option);
        });
      })
      .catch(error => {
        console.error('Error fetching nodes:', error);
        const nodeSelect = document.getElementById('nodeSelect');
        nodeSelect.innerHTML = '<option selected disabled>Error loading nodes</option>';
      });
  });
