package dk.steffenkarlsson.sofa.bdae.entity;

import com.google.gson.annotations.SerializedName;

import java.util.List;

/**
 * Created by steffenkarlsson on 6/2/16.
 */
public class Dataset {

    @SerializedName("name")
    protected String mName;

    @SerializedName("description")
    protected String mDescription;

    @SerializedName("operations")
    protected List<String> mOperations;

    public String getName() {
        return mName;
    }

    public String getDescription() {
        return mDescription;
    }

    public List<String> getOperations() {
        return mOperations;
    }
}
