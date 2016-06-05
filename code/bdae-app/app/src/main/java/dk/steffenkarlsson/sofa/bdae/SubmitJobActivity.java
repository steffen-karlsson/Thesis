package dk.steffenkarlsson.sofa.bdae;

import android.os.Handler;
import android.support.design.widget.Snackbar;
import android.text.Editable;
import android.text.SpannableString;
import android.text.Spanned;
import android.text.style.ForegroundColorSpan;
import android.view.LayoutInflater;
import android.view.View;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import android.widget.LinearLayout;
import android.widget.TextView;

import com.rengwuxian.materialedittext.MaterialEditText;

import java.util.ArrayList;
import java.util.List;

import butterknife.BindView;
import butterknife.OnClick;
import dk.steffenkarlsson.sofa.bdae.entity.Dataset;
import dk.steffenkarlsson.sofa.bdae.entity.Operation;
import dk.steffenkarlsson.sofa.bdae.extra.ChangedTextWatcher;
import dk.steffenkarlsson.sofa.bdae.extra.CustomRequestListener;
import dk.steffenkarlsson.sofa.bdae.extra.DatasetCache;
import dk.steffenkarlsson.sofa.bdae.extra.KeyboardHelper;
import dk.steffenkarlsson.sofa.bdae.recycler.SubmitNewJobRequest;
import dk.steffenkarlsson.sofa.networking.Result;
import fr.ganfra.materialspinner.MaterialSpinner;

/**
 * Created by steffenkarlsson on 6/2/16.
 */
public class SubmitJobActivity extends BaseConfigurationActivity {

    public enum RequestType {
        SUBMIT_JOB
    }

    @BindView(R.id.datasetDropdown)
    protected MaterialSpinner mDatasetDropdown;

    @BindView(R.id.operationDropdown)
    protected MaterialSpinner mOperationDropdown;

    @BindView(R.id.argumentWrapper)
    protected LinearLayout mArgumentWrapper;

    @BindView(R.id.argumentTitle)
    protected TextView mArgumentTitle;

    @BindView(R.id.submit)
    protected TextView mSubmit;

    private List<Dataset> mDatasets;
    private Dataset mSelectedDataset = null;
    private int mSelectedOperationIndex = -1;
    private List<String> mOperationArguments;

    @Override
    protected void onResume() {
        super.onResume();

        if (getSupportActionBar() != null)
            getSupportActionBar().setHomeAsUpIndicator(R.drawable.ic_clear_white);

        DatasetCache.getInstance().getDatasets(mActivityHandler, new DatasetCache.OnDatasetReadyListener() {
            @Override
            public void onReady(List<Dataset> datasets) {
                mDatasets = datasets;
                ArrayList<String> datasetNames = new ArrayList<>();
                for (Dataset dataset : mDatasets)
                    datasetNames.add(dataset.getName().trim());

                configureSpannableAdapter(datasetNames, mDatasetDropdown);
            }
        });

        mDatasetDropdown.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener() {
            @Override
            public void onItemSelected(AdapterView<?> parent, View view, int position, long id) {
                if (position >= 0) {
                    mSelectedDataset = mDatasets.get(position);

                    mOperationDropdown.setVisibility(View.VISIBLE);
                    configureSpannableAdapter(new ArrayList<>(mSelectedDataset.getOperationNames(false)), mOperationDropdown);
                }
            }

            @Override
            public void onNothingSelected(AdapterView<?> parent) {
                mOperationDropdown.setVisibility(View.INVISIBLE);
                mArgumentWrapper.setVisibility(View.INVISIBLE);
            }
        });

        mOperationDropdown.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener() {
            @Override
            public void onItemSelected(AdapterView<?> parent, View view, int position, long id) {
                if (position >= 0) {
                    mSelectedOperationIndex = position;
                    Operation operation = mSelectedDataset.getOperations().get(mSelectedOperationIndex);
                    if (!operation.hasArguments()) {
                        mArgumentWrapper.setVisibility(View.INVISIBLE);
                        mSubmit.setEnabled(true);
                        return;
                    }

                    mArgumentWrapper.setVisibility(View.VISIBLE);
                    mArgumentTitle.setText(operation.getNumArguments() == 1
                            ? R.string.hint_argument
                            : R.string.hint_arguments);

                    mOperationArguments = new ArrayList<>(operation.getNumArguments());
                    for (int i = 0; i < operation.getNumArguments(); i++) {
                        mOperationArguments.add(null);

                        final MaterialEditText editText = (MaterialEditText) LayoutInflater.from(getContext()).inflate(R.layout.input_text, null);
                        editText.addTextChangedListener(new ChangedTextWatcher(editText, i, new ChangedTextWatcher.OnValidateListener() {
                            @Override
                            public void onValidated(int index, boolean isValid, boolean hasChanged) {
                                mOperationArguments.set(index, editText.getText().toString());
                                SubmitJobActivity.this.validate();
                            }

                            @Override
                            public boolean validate(MaterialEditText editText, Editable s) {
                                return ChangedTextWatcher.emptyValidator(editText, s);
                            }
                        }));
                        mArgumentWrapper.addView(editText);

                        if (i == 0)
                            KeyboardHelper.showKeyboardForView(getContext(), editText);
                    }
                }
            }

            @Override
            public void onNothingSelected(AdapterView<?> parent) {
                mArgumentWrapper.setVisibility(View.INVISIBLE);
            }
        });
    }

    private void validate() {
        boolean notValidated = mOperationArguments == null || mOperationArguments.contains(null);
        mSubmit.setTextColor(getResources().getColor(notValidated
                ? R.color.colorPrimaryFaded
                : R.color.white));
        mSubmit.setEnabled(!notValidated);
    }

    private void configureSpannableAdapter(ArrayList<? extends String> dataList, MaterialSpinner dropDown) {
        final List<SpannableString> coloredData = new ArrayList<>();
        final int color = getResources().getColor(R.color.colorPrimary);

        for (String data : dataList) {
            SpannableString ss = new SpannableString(data);
            ss.setSpan(new ForegroundColorSpan(color), 0, data.length(),
                    Spanned.SPAN_INCLUSIVE_INCLUSIVE);
            coloredData.add(ss);
        }

        ArrayAdapter<SpannableString> adapter = new ArrayAdapter<>(
                mActivityHandler.getActivity(), android.R.layout.simple_spinner_item, coloredData);
        adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
        dropDown.setAdapter(adapter);
    }

    @OnClick(R.id.submit)
    protected void onSubmitClicked() {
        if (mSubmit.isEnabled()) {
            new SubmitNewJobRequest(
                    new SubmitNewJobRequest.NewJobObject(
                            mSelectedDataset.getName(),
                            mSelectedDataset.getOperations().get(mSelectedOperationIndex).getName(),
                            mOperationArguments))
                    .withContext(getActivity())
                    .setOnRequestListener(new CustomRequestListener(mActivityHandler) {
                        @Override
                        protected void onData(int id, Result result) {
                            String text = getResources().getString(R.string.job_submitted);
                            SpannableString ss = new SpannableString(text);
                            ss.setSpan(new ForegroundColorSpan(getResources().getColor(R.color.colorPrimary)), 0, text.length(),
                                    Spanned.SPAN_INCLUSIVE_INCLUSIVE);
                            Snackbar.make(findViewById(android.R.id.content), ss, Snackbar.LENGTH_SHORT).show();

                            new Handler().postDelayed(new Runnable() {
                                @Override
                                public void run() {
                                    SubmitJobActivity.this.finish();
                                }
                            }, 1000);
                        }

                        @Override
                        public void onError(int id, int statusCode) {
                            //TODO: Handle error
                        }
                    })
                    .run(RequestType.SUBMIT_JOB);
        }
    }

    @Override
    protected boolean requiresConfiguration() {
        return true;
    }

    @Override
    protected int getLayoutResource() {
        return R.layout.activity_submit_job;
    }

    @Override
    protected boolean showBackButton() {
        return true;
    }

    @Override
    protected int getTitleResource() {
        return R.string.actionbar_submit_job;
    }
}
