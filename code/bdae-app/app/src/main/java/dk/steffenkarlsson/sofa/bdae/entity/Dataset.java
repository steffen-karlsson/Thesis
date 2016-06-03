package dk.steffenkarlsson.sofa.bdae.entity;

import com.google.gson.annotations.SerializedName;

import java.util.ArrayList;
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

    protected transient boolean mIsEven;

    public boolean isEven() {
        return mIsEven;
    }

    public void setEven(boolean isEven) {
        this.mIsEven = isEven;
    }

    public String getName() {
        return mName;
    }

    public String getDescription() {
        return mDescription;
    }

    public List<String> getOperations(boolean withNewLine) {
        if (mOperations == null)
            return new ArrayList<>();

        if (!withNewLine)
            return mOperations;

        ArrayList<String> modifiedOperations = new ArrayList<>();
        modifiedOperations.add("");
        for (int i = 0; i < mOperations.size(); i++) {
            String operation = mOperations.get(i);
            modifiedOperations.add(String.format("%s" + (i != mOperations.size() - 1 ? "\n" : ""), operation));
        }
        return modifiedOperations;
    }
}
