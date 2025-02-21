document.addEventListener("DOMContentLoaded", function () {
  let currentStep = 1;
  const totalSteps = 3;
  const toggleCheckbox = document.getElementById("toggleAdditionalImages");

  // Confirmation dialog handling
  const confirmationModal = document.getElementById("confirmationModal");
  const confirmSubmitBtn = document.getElementById("confirmSubmit");
  const cancelSubmitBtn = document.getElementById("cancelSubmit");
  const registerForm = document.getElementById("registerStudentForm");

  // Handle form submission with confirmation
  registerForm.addEventListener("submit", function (e) {
    e.preventDefault();
    confirmationModal.classList.add("is-active");
  });

  // Confirm submission
  confirmSubmitBtn.addEventListener("click", function () {
    confirmationModal.classList.remove("is-active");
    registerForm.submit();
  });

  // Cancel submission
  cancelSubmitBtn.addEventListener("click", function () {
    confirmationModal.classList.remove("is-active");
  });

  // Close modal when clicking background or close button
  confirmationModal.querySelector(".modal-background, .delete").addEventListener("click", function () {
    confirmationModal.classList.remove("is-active");
  });

  // Get the input field
  const agentCodeInput = document.querySelector("input[name='display_agent']");
  const nameInput = document.querySelector("input[name='name']");
  const addressInput = document.querySelector("textarea[name='address']");
  const idNoInput = document.querySelector("input[name='id_no']");
  const phoneNumbersInput = document.querySelector("input[name='phone_numbers']");
  const emailInput = document.querySelector("input[name='email']");
  const contactNoEmergencyInput = document.querySelector("input[name='contact_no_emergency']");
  const emergencyContactRelationshipInput = document.querySelector("input[name='emergency_contact_relationship']");

  nameInput.addEventListener("input", function () {
    this.value = this.value.toUpperCase().replace(/[^A-Za-z'\s]/g, "");
  });

  idNoInput.addEventListener("input", function () {
    this.value = this.value.replace(/[^0-9]/g, "");
  });

  addressInput.addEventListener("input", function () {
    this.value = this.value.toUpperCase().replace(/[^A-Z0-9\s]/g, "");
  });

  // Phone Numbers Input (Numbers Only)
  phoneNumbersInput.addEventListener("input", function () {
    this.value = this.value.replace(/[^0-9]/g, ""); // Remove non-numeric characters
  });

  // Email Input (Force Uppercase)
  emailInput.addEventListener("input", function () {
    this.value = this.value.toUpperCase();
  });

  // Contact No Emergency Input (Numbers Only)
  contactNoEmergencyInput.addEventListener("input", function () {
    this.value = this.value.replace(/[^0-9]/g, ""); // Remove non-numeric characters
  });

  // Emergency Contact Relationship Input (Force Uppercase)
  emergencyContactRelationshipInput.addEventListener("input", function () {
    this.value = this.value.toUpperCase().replace(/[^A-Za-z]/g, "");
  });

  // Add the event listener outside the function
  agentCodeInput.addEventListener("input", function () {
    // Get the current value of the input field
    let inputValue = this.value;

    // Convert to uppercase and remove any non-numeric characters
    inputValue = inputValue.toUpperCase().replace(/[^A-Z0-9]/g, "");

    // Update the input field with the sanitized value
    this.value = inputValue;
  });

  function showStep(step) {
    // Update step visibility
    for (let i = 1; i <= totalSteps; i++) {
      document.getElementById(`step${i}`).style.display = i === step ? "block" : "none";
    }

    // Update progress bar
    updateProgressBar(step);
  }

  function updateProgressBar(currentStep) {
    // Update step numbers
    const stepNumbers = document.querySelectorAll(".step-number");
    stepNumbers.forEach((step, index) => {
      if (index < currentStep) {
        step.classList.add("active");
      } else {
        step.classList.remove("active");
      }
    });

    // Update progress line
    const progressFill = document.querySelector(".progress-fill");
    const progressPercent = ((currentStep - 1) / (totalSteps - 1)) * 100;
    progressFill.style.width = `${progressPercent}%`;
  }

  function validateAgentCode() {
    const agentCode = document.querySelector("input[name='display_agent']").value.toLowerCase();
    const termsAcknowledgment = document.querySelector("input[name='terms_acknowledgment']").checked;
    const selectedForm = document.querySelector("input[name='registration_form']:checked");

    if (!termsAcknowledgment) {
      alert("You must acknowledge the terms and conditions before proceeding.");
      return;
    }

    if (!selectedForm) {
      alert("Please select a registration form.");
      return;
    }

    fetch(`/validate-agent-code/?agent_code=${agentCode}`)
      .then((response) => response.json())
      .then((data) => {
        if (data.valid) {
          currentStep++;
          showStep(currentStep);
        } else {
          alert("Invalid agent code. Please enter a valid agent code.");
        }
      });
  }

  function validateIdNo() {
    const idNo = document.querySelector("input[name='id_no']").value;

    // 1. Basic Length Check (Must be 12 digits)
    if (idNo.length !== 12) {
      alert("IC number must be exactly 12 digits.");
      return false;
    }

    // 2. Check if all characters are digits
    if (!/^\d+$/.test(idNo)) {
      alert("IC number must contain only digits.");
      return false;
    }

    // 3.  Now proceed with the server-side validation (if needed)
    return fetch(`/validate-id-no/?id_no=${idNo}`)
      .then((response) => response.json())
      .then((data) => {
        if (data.exists) {
          alert("A student with this IC number already exists. Please use a different IC number.");
          return false;
        }
        return true;
      });
  }

  function validateStep2() {
    const nameInput = document.querySelector("input[name='name']");
    const idNoInput = document.querySelector("input[name='id_no']");
    const addressTextarea = document.querySelector("textarea[name='address']");
    const selectedGender = document.querySelector("input[name='gender']:checked");

    if (nameInput.value.trim() === "") {
      alert("Please enter your name.");
      nameInput.focus(); // Set focus to the name input
      return false; // Indicate validation failed
    }

    if (idNoInput.value.trim() === "") {
      alert("Please enter your ID number.");
      idNoInput.focus(); // Set focus to the ID number input
      return false; // Indicate validation failed
    }

    if (addressTextarea.value.trim() === "") {
      alert("Please enter your address.");
      addressTextarea.focus(); // Set focus to the address input
      return false; // Indicate validation failed
    }

    if (!selectedGender) {
      alert("Please select a gender.");
      return false;
    }

    return true; // Validation successful
  }

  document.querySelectorAll(".nextStep").forEach((button) => {
    button.addEventListener("click", function () {
      if (currentStep === 1) {
        validateAgentCode();
      } else if (currentStep === 2) {
        validateIdNo().then((isValid) => {
          if (isValid) {
            if (validateStep2()) {
              // Validate step 2 after ID validation
              currentStep++;
              showStep(currentStep);
            }
          }
        });
      } else if (currentStep < totalSteps) {
        currentStep++;
        showStep(currentStep);
      }
    });
  });

  document.querySelectorAll(".prevStep").forEach((button) => {
    button.addEventListener("click", function () {
      if (currentStep > 1) {
        currentStep--;
        showStep(currentStep);
      }
    });
  });

  showStep(currentStep);

  $(document).ready(function () {
    // Initialize the Slick carousel
    $(".image-carousel").slick({
      slidesToShow: 1,
      slidesToScroll: 1,
      arrows: true,
      dots: true,
      adaptiveHeight: true,
    });

    // Store mapping of inputs to carousel slides
    let imageMap = {};

    function updateCarousel(imageSrc, inputId) {
      const slickInstance = $(".image-carousel").slick("getSlick");

      if (imageMap[inputId] !== undefined) {
        // Replace the existing image
        const slideIndex = imageMap[inputId];
        let existingSlide = $(`.image-carousel .slick-slide[data-input-id="${inputId}"]`);

        if (existingSlide.length) {
          existingSlide.find("img").attr("src", imageSrc);
        }
      } else {
        // Otherwise, add a new slide and store index
        const newIndex = slickInstance.slideCount;
        $(".image-carousel").slick(
          "slickAdd",
          `
                <div class="carousel-slide slick-slide" data-input-id="${inputId}">
                    <img src="${imageSrc}" class="carousel-image">

                </div>`
        );
        imageMap[inputId] = newIndex;
      }
    }

    document.querySelectorAll(".uploadImageForm").forEach((input) => {
      input.addEventListener("change", function () {
        const file = input.files[0];
        if (file) {
          const reader = new FileReader();
          reader.onload = function (e) {
            updateCarousel(e.target.result, input.id);

            // Change the icon to indicate an image is attached
            const icon = document.querySelector(`.uploadIcon[data-input-id="${input.id}"]`);
            icon.innerHTML = "&#9989;"; // Change to a different icon
            icon.style.color = "#28a745"; // Change color to green
          };
          reader.readAsDataURL(file);
        }
      });
    });

    // Event delegation to handle rotate button clicks
    $(".image-carousel").on("click", ".rotate-image", function () {
      const image = $(this).prev("img")[0];
      rotateImage(image);
    });

    // Event listeners for upload icons
    document.querySelectorAll(".uploadIcon").forEach((icon) => {
      icon.addEventListener("click", function () {
        const inputId = this.dataset.inputId;
        document.getElementById(inputId).click();
      });
    });

    // Update the toggleCheckbox event listener
    toggleCheckbox.addEventListener("change", function () {
      document.querySelectorAll(".uploadItem.additional").forEach((item) => {
        item.style.display = this.checked ? "block" : "none";
      });
    });
  });

  function fetchRegistrationForms(selectedClassIds) {
    const registrationFormContainer = document.getElementById("registration-form-container");
    if (selectedClassIds.length === 0) {
      registrationFormContainer.innerHTML = "<p>Select a class first...</p>";
      return;
    }

    fetch(`/get-registration-forms/?class_id[]=${selectedClassIds.join("&class_id[]=")}`)
      .then((response) => response.json())
      .then((data) => {
        if (data.registration_forms.length === 0) {
          registrationFormContainer.innerHTML = "<p>No registration forms available for the selected class.</p>";
        } else {
          registrationFormContainer.innerHTML = data.registration_forms
            .map(
              (form) => `
                <div class="form-check" style="margin-bottom: 15px;">
                  <input class="form-check-input" type="radio" name="registration_form" id="registration_form_${form.id}" value="${form.id}">
                  <label class="form-check-label" for="registration_form_${form.id}">
                    ${form.name}
                  </label>
                  <a href="#" class="view-terms" data-form-id="${form.id}" style="text-decoration: underline;">View Terms</a>
                </div>
              `
            )
            .join("");

          document.querySelectorAll(".view-terms").forEach((link) => {
            link.addEventListener("click", function (e) {
              e.preventDefault();
              fetch(`/get_terms/?form_id=${this.dataset.formId}`)
                .then((response) => response.json())
                .then((data) => {
                  document.getElementById("termsModalContent").innerHTML = data.terms.map((term) => `<p>${term.content}</p>`).join("");
                  document.getElementById("termsModal").classList.add("is-active");
                })
                .catch((error) => console.error("Error fetching terms:", error));
            });
          });
        }
      })
      .catch((error) => console.error("Error fetching registration forms:", error));
  }

  document.querySelectorAll("input[name='class_id']").forEach((checkbox) => {
    checkbox.addEventListener("change", function () {
      const selectedClassIds = Array.from(document.querySelectorAll("input[name='class_id']:checked")).map((cb) => cb.value);
      fetchRegistrationForms(selectedClassIds);
    });
  });

  document.querySelectorAll(".modal-close, .modal-background, .modal-card-foot .button").forEach((element) => {
    element.addEventListener(
      "click",
      function () {
        document.getElementById("termsModal").classList.remove("is-active");
      },
      { passive: true }
    );
  });
});
