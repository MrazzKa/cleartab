/**
 * ClearTab survey and sign-up forms (Google Apps Script).
 *
 * How to use:
 *   1. Open https://script.google.com while signed in to the Google account that should own the forms
 *      (preferably the UA Google account, kamarayev@arizona.edu).
 *   2. New project -> paste this whole file -> Save -> select createClearTabForms -> Run.
 *   3. Approve the permission prompt (it only creates forms in your Drive).
 *   4. Open View -> Logs (or Execution log): it prints the edit and share links of both forms.
 *
 * Two separate forms on purpose:
 *   - Survey: anonymous, no names or emails, no documents.
 *   - Sign-up: optional contact for testing, free help with a current bill, or an interview.
 *     Linked from the survey's thank-you message, so contact details are never stored next to survey answers.
 */

function createClearTabForms() {
  var signup = buildSignupForm_();
  var survey = buildSurveyForm_(signup.getPublishedUrl());
  publish_(signup);
  publish_(survey);
  Logger.log('SURVEY share link: ' + survey.getPublishedUrl());
  Logger.log('SURVEY edit link:  ' + survey.getEditUrl());
  Logger.log('SIGN-UP share link: ' + signup.getPublishedUrl());
  Logger.log('SIGN-UP edit link:  ' + signup.getEditUrl());
}

function publish_(form) {
  // Newer Forms have an explicit "published" state; older accounts publish on creation.
  try {
    form.setPublished(true);
  } catch (e) {
    Logger.log('setPublished not available, form is published by default: ' + e);
  }
}

function buildSurveyForm_(signupUrl) {
  var form = FormApp.create('ClearTab: medical bills survey (5 minutes, anonymous)');
  form.setDescription(
    'We are a University of Arizona student team (ISTA 498 capstone, Team Trace) building ClearTab, a free, ' +
    'open-source tool that helps people check a medical bill and find out whether they owe it, should wait, ' +
    'or should question it.\n\n' +
    'This survey takes about 5 minutes. It is anonymous: we do not ask for your name, email, or any documents. ' +
    'Please do not type names, account numbers, or diagnoses in the text boxes. You can skip any question ' +
    'and stop at any time. You must be 18 or older.\n\n' +
    'Questions: Timur Kamarayev, kamarayev@arizona.edu. Faculty: Dr. Lingyao Li (advisor), ' +
    'Michael McKisson (instructor).'
  );
  form.setCollectEmail(false);
  form.setAllowResponseEdits(false);
  form.setShowLinkToRespondAgain(false);
  form.setProgressBar(true);

  // Page 1: eligibility
  var age = form.addMultipleChoiceItem()
    .setTitle('Are you 18 or older?')
    .setRequired(true);

  // Page 2: about you
  var pAbout = form.addPageBreakItem().setTitle('About you');
  form.addMultipleChoiceItem()
    .setTitle('Which describes you best?')
    .setChoiceValues([
      'UA undergraduate student',
      'UA graduate student',
      'UA staff or faculty',
      'Student at another school',
      'Not a student, living in Arizona',
      'Not a student, living outside Arizona'
    ])
    .showOtherOption(true)
    .setRequired(true);
  form.addMultipleChoiceItem()
    .setTitle('Are you an international student or scholar?')
    .setChoiceValues(['Yes', 'No', 'Prefer not to say']);
  form.addMultipleChoiceItem()
    .setTitle('What health coverage do you have now?')
    .setChoiceValues([
      'UA Student Health Insurance Plan (SHIP)',
      "A parent's or family member's plan",
      'My own or my spouse\'s employer plan',
      'AHCCCS (Arizona Medicaid) or KidsCare',
      'Marketplace plan (healthcare.gov)',
      'Medicare',
      'International or travel insurance',
      'No insurance',
      'Not sure'
    ])
    .showOtherOption(true);

  // Page 3: bills in the last 2 years
  var pBills = form.addPageBreakItem().setTitle('Medical bills in the last 2 years');
  var gotBill = form.addMultipleChoiceItem()
    .setTitle('In the last 2 years, did you receive a bill for medical, dental, ambulance or mental health care?')
    .setRequired(true);

  // Page 4: details (only if they got a bill)
  var pDetails = form.addPageBreakItem().setTitle('About those bills');
  form.addCheckboxItem()
    .setTitle('What kind of care were the bills for? (choose all that apply)')
    .setChoiceValues([
      'Emergency room',
      'Ambulance',
      'Urgent care',
      'Campus Health',
      'Doctor visit or specialist',
      'Lab tests or imaging (X-ray, MRI, CT)',
      'Surgery or hospital stay',
      'Dental',
      'Mental health',
      'Prescription drugs'
    ])
    .showOtherOption(true);
  form.addMultipleChoiceItem()
    .setTitle('What was the largest single bill you received (amount you were asked to pay)?')
    .setChoiceValues(['Under $100', '$100 - $499', '$500 - $1,999', '$2,000 - $9,999', '$10,000 or more', 'Do not remember']);
  form.addMultipleChoiceItem()
    .setTitle('How many separate bills did you get for that one visit or event?')
    .setChoiceValues(['1', '2 - 3', '4 or more', 'Do not know']);
  form.addScaleItem()
    .setTitle('How easy was it to understand what you owed and why?')
    .setBounds(1, 5)
    .setLabels('Very hard', 'Very easy');
  form.addMultipleChoiceItem()
    .setTitle('Did you ever think one of those bills might be wrong?')
    .setChoiceValues(['Yes, and I was sure', 'Yes, I suspected it', 'No', 'Not sure']);
  form.addMultipleChoiceItem()
    .setTitle('Did you ever pay a bill even though you were not sure it was correct?')
    .setChoiceValues(['Yes', 'No', 'Not sure']);
  form.addCheckboxItem()
    .setTitle('What did you do about the bill(s)? (choose all that apply)')
    .setChoiceValues([
      'Paid in full',
      'Set up a payment plan',
      'Called the hospital or doctor billing office',
      'Called my insurance company',
      'Asked for an itemized bill',
      'Applied for financial assistance (charity care)',
      'Disputed or appealed it',
      'Asked family or friends for help',
      'Have not paid yet / ignored it',
      'It went to a collection agency'
    ])
    .showOtherOption(true);
  form.addMultipleChoiceItem()
    .setTitle('Did anything you did lower the amount you had to pay?')
    .setChoiceValues(['Yes', 'No', 'Still in progress', 'Did not try']);
  form.addParagraphTextItem()
    .setTitle('Optional: what was the most confusing or frustrating part? (no names, numbers or diagnoses please)');

  // Page 5: what people know
  var pKnow = form.addPageBreakItem().setTitle('What you know');
  var knowGrid = form.addGridItem()
    .setTitle('Before today, had you heard of these?')
    .setRows([
      'Explanation of Benefits (EOB) from an insurer',
      'Itemized bill with billing codes',
      'Hospital financial assistance / charity care (free or discounted care based on income)',
      'No Surprises Act (protection from surprise out-of-network bills)',
      'Good Faith Estimate for people paying without insurance',
      'Hospital price transparency files'
    ])
    .setColumns(['Never heard of it', 'Heard of it', 'Know how to use it']);
  form.addMultipleChoiceItem()
    .setTitle('If an insurer sends you an EOB, what do you usually do with it?')
    .setChoiceValues(['Read and compare it with the bill', 'Glance at it', 'Ignore it', 'I have never received one', 'Not sure what it is']);

  // Page 6: what would help
  var pHelp = form.addPageBreakItem().setTitle('What would help');
  form.addCheckboxItem()
    .setTitle('Which would help you most? (choose up to 3)')
    .setChoiceValues([
      'Tell me in plain words whether I owe this bill, should wait, or should question it',
      'Find errors in my bill (duplicates, wrong amounts, charges my insurer did not approve)',
      'Tell me if I qualify for free or discounted hospital care, and help me apply',
      'Write the letter or tell me what to say when I call',
      'Explain my insurance (deductible, coinsurance, network) using my own bill',
      'Help me appeal a denied insurance claim',
      'Show what a fair price would be for my service',
      'Explain the bill in my own language',
      'Remind me about deadlines and keep all papers from one visit together'
    ])
    .setValidation(FormApp.createCheckboxValidation().requireSelectAtMost(3).build());
  form.addMultipleChoiceItem()
    .setTitle('Would you take a photo of your bill to have a free tool check it, if the photo is not stored?')
    .setChoiceValues(['Yes', 'Maybe, depends on who runs it', 'No']);
  form.addCheckboxItem()
    .setTitle('What would make you trust a tool like this? (choose all that apply)')
    .setChoiceValues([
      'Run by a university team',
      'Free with no ads',
      'Open-source code',
      'No account needed',
      'Shows the official source for every finding',
      'A human can review my case',
      'Recommended by Campus Health or a trusted person'
    ])
    .showOtherOption(true);
  form.addMultipleChoiceItem()
    .setTitle('Which language would you prefer for an app like this?')
    .setChoiceValues(['English', 'Spanish', 'Chinese', 'Arabic', 'Hindi', 'Russian', 'Korean', 'Vietnamese'])
    .showOtherOption(true);
  form.addParagraphTextItem()
    .setTitle('Optional: anything else we should know?');

  // Branching
  age.setChoices([
    age.createChoice('Yes', pAbout),
    age.createChoice('No', FormApp.PageNavigationType.SUBMIT)
  ]);
  gotBill.setChoices([
    gotBill.createChoice('Yes', pDetails),
    gotBill.createChoice('No', pKnow),
    gotBill.createChoice('Not sure', pDetails)
  ]);

  form.setConfirmationMessage(
    'Thank you! Your answers help us build ClearTab.\n\n' +
    'Want to try the app, get free help checking a bill you have now, or talk to us for 15 minutes? ' +
    'Leave a contact here (separate form, not linked to your answers): ' + signupUrl
  );
  return form;
}

function buildSignupForm_() {
  var form = FormApp.create('ClearTab: try the app or get free help with a bill');
  form.setDescription(
    'ClearTab is a free, open-source tool from a University of Arizona student team (ISTA 498, Team Trace). ' +
    'This form is separate from the survey; your survey answers are not linked to it.\n\n' +
    'We only use your contact to schedule what you choose below and delete it after the project ends ' +
    '(December 2026). Please do not upload or type any medical details here. If you want help with a bill, ' +
    'we will meet you (in person or video) and go through it together only with your permission; ' +
    'we do not keep copies.\n\n' +
    'ClearTab is a student project, not legal or medical advice. Questions: kamarayev@arizona.edu.'
  );
  form.setCollectEmail(false);
  form.setProgressBar(false);

  form.addMultipleChoiceItem()
    .setTitle('Are you 18 or older?')
    .setChoiceValues(['Yes', 'No'])
    .setRequired(true);
  form.addCheckboxItem()
    .setTitle('What would you like? (choose all that apply)')
    .setChoiceValues([
      'Try the app and give feedback (about 20 minutes, in person or video)',
      'Get free help checking a medical bill I have now',
      'Talk to the team about my experience with medical bills (about 15 minutes)',
      'Get a message when the public version is ready'
    ])
    .setRequired(true);
  form.addTextItem()
    .setTitle('First name or nickname')
    .setRequired(true);
  form.addTextItem()
    .setTitle('Email or phone number')
    .setRequired(true);
  form.addMultipleChoiceItem()
    .setTitle('If you have a bill now: roughly how much is it?')
    .setChoiceValues(['Under $100', '$100 - $499', '$500 - $1,999', '$2,000 - $9,999', '$10,000 or more', 'I do not have a bill now']);
  form.addMultipleChoiceItem()
    .setTitle('If you have a bill now: did you also get an EOB from your insurer?')
    .setChoiceValues(['Yes', 'No', 'I have no insurance', 'Not sure']);
  form.addCheckboxItem()
    .setTitle('How would you prefer to meet?')
    .setChoiceValues(['In person on the UA campus', 'Video call', 'Phone']);
  form.addCheckboxItem()
    .setTitle('Preferred language')
    .setChoiceValues(['English', 'Spanish', 'Russian'])
    .showOtherOption(true);
  form.addMultipleChoiceItem()
    .setTitle('If ClearTab helps you lower or correct a bill, may we contact you later to ask whether you would ' +
      'share your story (anonymously or by first name) at the UA iShowcase on December 10? You can say no later.')
    .setChoiceValues(['Yes, you may ask me', 'No']);

  form.setConfirmationMessage('Thank you! A team member will contact you within a few days.');
  return form;
}
