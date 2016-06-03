package dk.steffenkarlsson.sofa.bdae.entity;

import com.google.gson.annotations.SerializedName;

import java.util.ArrayList;
import java.util.List;

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

    public String getName() {
        return mName;
    }

    public String getIdentifier() {
        return mIdentifier;
    }

    public String getDatasetName() {
        return mDatasetName;
    }

    public List<String> getParameters() {
        return mParameters == null ? new ArrayList<String>() : mParameters;
    }

    public String getDataType() {
        return mDataType;
    }

    public Status getStatus() {
        return Status.values()[mStatus];
    }
}
