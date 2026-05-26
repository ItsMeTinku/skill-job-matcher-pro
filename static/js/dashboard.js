// Enhanced dashboard JS with manual page support and delete operations
document.addEventListener('DOMContentLoaded', function () {

  // ── Handle skill form submission on manual page ──────────────────────
  const manualSkillForm = document.getElementById('manual-skill-form');
  if (manualSkillForm) {
    manualSkillForm.addEventListener('submit', async function (ev) {
      ev.preventDefault();
      const skillInput = document.getElementById('skill-input');
      const skill = skillInput.value && skillInput.value.trim();
      
      if (!skill) {
        alert('Please enter a skill');
        return;
      }

      const payload = {
        skill: skill,
        resume_id: '',
      };

      try {
        const resp = await fetch(manualSkillForm.action, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
          },
          body: JSON.stringify(payload),
        });

        const data = await resp.json();
        if (resp.ok && data.ok) {
          skillInput.value = '';
          // Reload page to show updated skills and matches
          window.location.reload();
        } else {
          alert((data && data.error) || 'Failed to add skill.');
        }
      } catch (err) {
        console.error('Error adding skill:', err);
        alert('Network error while adding skill.');
      }
    });
  }

  // ── Handle skill removal forms (AJAX for instant removal) ───────────
  const removeSkillForms = document.querySelectorAll('.skill-remove-form');
  removeSkillForms.forEach(form => {
    form.addEventListener('submit', async function (ev) {
      ev.preventDefault();
      
      if (!confirm('Remove this skill?')) {
        return;
      }

      const skillId = form.querySelector('input[name="skill_id"]').value;
      
      try {
        const resp = await fetch(form.action || '/dashboard/skills/remove', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
          },
          body: JSON.stringify({ skill_id: skillId }),
        });

        if (resp.ok) {
          // Reload to update skills list and matches
          window.location.reload();
        } else {
          alert('Failed to remove skill.');
        }
      } catch (err) {
        console.error('Error removing skill:', err);
        alert('Network error while removing skill.');
      }
    });
  });

  // ── Handle delete resume buttons with confirmation ──────────────────
  const deleteResumeButtons = document.querySelectorAll('.delete-resume-btn');
  deleteResumeButtons.forEach(btn => {
    btn.addEventListener('click', function (ev) {
      const filename = btn.getAttribute('data-filename') || 'this resume';
      const confirmed = confirm(
        'Are you sure you want to delete "' + filename + '"?\n\nThis action cannot be undone and all associated matches will be deleted.'
      );
      if (!confirmed) {
        ev.preventDefault();
      }
    });
  });

  // ── Handle "Check Jobs" action on old skills page ───────────────────
  const checkBtn = document.getElementById('skill-check-btn');
  const checkForm = document.getElementById('skill-check-form');
  if (checkBtn && checkForm) {
    checkBtn.addEventListener('click', function (ev) {
      const skillInput = document.getElementById('skill-input');
      const resumeSelect = document.getElementById('resume-select');
      const tempField = document.getElementById('temp-skill-field');
      const resumeField = document.getElementById('temp-resume-field');
      tempField.value = skillInput.value && skillInput.value.trim();
      resumeField.value = resumeSelect ? resumeSelect.value : '';
      checkForm.submit();
    });
  }

});

      resumeField.value = resumeSelect ? resumeSelect.value : '';
      checkForm.submit();
    });
  }
});
