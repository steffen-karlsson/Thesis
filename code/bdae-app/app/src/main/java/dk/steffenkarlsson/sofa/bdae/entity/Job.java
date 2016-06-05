package dk.steffenkarlsson.sofa.bdae.entity;

import android.text.TextUtils;

import com.google.gson.annotations.SerializedName;

import java.util.ArrayList;
import java.util.List;

import dk.steffenkarlsson.sofa.bdae.recycler.SubmittedJobRecyclerView;

/**
 * Created by steffenkarlsson on 6/3/16.
 */
public class Job {

    public static enum Status {
        Processing, Done
    }

    @SerializedName("name")
    protected String mName;

    @SerializedName("identifier")
    protected String mIdentifier;

    @SerializedName("dataset_name")
    protected String mDatasetName;

    @SerializedName("status")
    protected int mStatus;

    @SerializedName("parameters")
    protected List<String> mParameters;

    @SerializedName("data_type")
    protected String mDataType;

    @SerializedName("result")
    protected String mResult;

    private SubmittedJobRecyclerView.OnClickListener mOnClickListener;

    public String getName() {
        return mName;
    }

    public String getIdentifier() {
        return mIdentifier;
    }

    public String getDatasetName() {
        return mDatasetName;
    }

    public List<String> getParameters(boolean withNewLine) {
        if (mParameters == null)
            return new ArrayList<>();

        if (!withNewLine)
            return mParameters;

        ArrayList<String> modifiedParameters = new ArrayList<>();
        for (int i = 0; i < mParameters.size(); i++) {
            String operation = mParameters.get(i);
            modifiedParameters.add(String.format("%s" + (i != mParameters.size() - 1 ? "\n" : ""), operation));
        }
        return modifiedParameters;
    }

    public String getDataType() {
        return mDataType;
    }

    public Status getStatus() {
        return Status.values()[mStatus];
    }

    public boolean hasResult() {
        return !TextUtils.isEmpty(mResult);
    }

    public String getResult() {
        return mResult;
    }

    public SubmittedJobRecyclerView.OnClickListener getOnClickListener() {
        return mOnClickListener;
    }

    public void setOnClickListener(SubmittedJobRecyclerView.OnClickListener onClickListener) {
        this.mOnClickListener = onClickListener;
    }
}
